package com.tea.mixer.ble;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattService;
import android.bluetooth.BluetoothManager;
import android.bluetooth.BluetoothProfile;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.util.Log;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.annotation.Keep;

import com.flet.serious_python_android.PythonActivity;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.UUID;

@Keep
public final class BleBridge {
    private static final String TAG = "TeaMixerBLE";
    private static final int REQUEST_CODE = 1001;
    private static final int UART_CHUNK_SIZE = 20;
    private static final long WRITE_TIMEOUT_MS = 3000;
    private static final UUID WRITE_UUID =
        UUID.fromString("0000ffe1-0000-1000-8000-00805f9b34fb");

    public static final int STATE_IDLE = 0;
    public static final int STATE_CONNECTING = 1;
    public static final int STATE_DISCOVERING = 2;
    public static final int STATE_CONNECTED = 3;
    public static final int STATE_FAILED = 4;

    private static volatile int state = STATE_IDLE;
    private static volatile String error = "";
    private static volatile BluetoothGatt gatt;
    private static volatile BluetoothGattCharacteristic writeCharacteristic;
    private static final Object WRITE_LOCK = new Object();
    private static volatile boolean writeCompleted;
    private static volatile int writeStatus = BluetoothGatt.GATT_FAILURE;

    private BleBridge() {}

    private static Activity activity() {
        Activity current = PythonActivity.mActivity;
        if (current == null) {
            throw new IllegalStateException("Android Activity is not ready");
        }
        return current;
    }

    private static BluetoothAdapter adapter() {
        BluetoothManager manager = (BluetoothManager)
            activity().getSystemService(Context.BLUETOOTH_SERVICE);
        if (manager == null || manager.getAdapter() == null) {
            throw new IllegalStateException("Bluetooth is not supported");
        }
        return manager.getAdapter();
    }

    private static String[] requiredPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            return new String[] {
                Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_CONNECT,
            };
        }
        return new String[] {Manifest.permission.ACCESS_FINE_LOCATION};
    }

    public static boolean hasPermissions() {
        Activity current = activity();
        for (String permission : requiredPermissions()) {
            if (ContextCompat.checkSelfPermission(current, permission)
                != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        return true;
    }

    public static void requestPermissions() {
        final Activity current = activity();
        final List<String> missing = new ArrayList<>();
        for (String permission : requiredPermissions()) {
            if (ContextCompat.checkSelfPermission(current, permission)
                != PackageManager.PERMISSION_GRANTED) {
                missing.add(permission);
            }
        }
        Log.i(TAG, "Missing permissions: " + missing);
        if (missing.isEmpty()) {
            return;
        }
        current.runOnUiThread(() -> ActivityCompat.requestPermissions(
            current,
            missing.toArray(new String[0]),
            REQUEST_CODE
        ));
    }

    public static boolean isBluetoothEnabled() {
        return adapter().isEnabled();
    }

    public static String[] pairedDevices() {
        if (!hasPermissions()) {
            throw new SecurityException("Bluetooth permissions are not granted");
        }
        Set<BluetoothDevice> bonded = adapter().getBondedDevices();
        if (bonded == null || bonded.isEmpty()) {
            return new String[0];
        }
        List<String> result = new ArrayList<>();
        for (BluetoothDevice device : bonded) {
            String name = device.getName();
            if (name == null || name.isEmpty()) {
                name = device.getAddress();
            }
            result.add(device.getAddress() + "\t" + name);
        }
        Log.i(TAG, "Paired devices: " + result.size());
        return result.toArray(new String[0]);
    }

    public static synchronized void connect(String address) {
        disconnect();
        error = "";
        state = STATE_CONNECTING;
        Log.i(TAG, "Connecting to " + address);
        try {
            BluetoothDevice device = adapter().getRemoteDevice(address);
            gatt = device.connectGatt(
                activity().getApplicationContext(),
                false,
                CALLBACK,
                BluetoothDevice.TRANSPORT_LE
            );
            if (gatt == null) {
                fail("Could not start GATT connection");
            }
        } catch (Exception exception) {
            Log.e(TAG, "Connect failed", exception);
            fail(exception.toString());
        }
    }

    public static int connectionState() {
        return state;
    }

    public static String lastError() {
        return error == null ? "" : error;
    }

    public static boolean writeUtf8(String value) {
        BluetoothGatt currentGatt = gatt;
        BluetoothGattCharacteristic characteristic = writeCharacteristic;
        if (state != STATE_CONNECTED || currentGatt == null || characteristic == null) {
            error = "No active GATT connection";
            return false;
        }
        try {
            byte[] payload = value.getBytes(StandardCharsets.UTF_8);
            Log.i(TAG, "Writing UART payload, bytes=" + payload.length);
            for (int offset = 0; offset < payload.length; offset += UART_CHUNK_SIZE) {
                int end = Math.min(offset + UART_CHUNK_SIZE, payload.length);
                byte[] chunk = Arrays.copyOfRange(payload, offset, end);
                synchronized (WRITE_LOCK) {
                    writeCompleted = false;
                    writeStatus = BluetoothGatt.GATT_FAILURE;

                    boolean accepted;
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        int result = currentGatt.writeCharacteristic(
                            characteristic,
                            chunk,
                            BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
                        );
                        accepted = result == BluetoothGatt.GATT_SUCCESS;
                    } else {
                        characteristic.setWriteType(
                            BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
                        );
                        characteristic.setValue(chunk);
                        accepted = currentGatt.writeCharacteristic(characteristic);
                    }
                    Log.i(
                        TAG,
                        "UART chunk offset=" + offset
                            + ", bytes=" + chunk.length
                            + ", accepted=" + accepted
                    );
                    if (!accepted) {
                        error = "UART chunk was rejected at offset " + offset;
                        return false;
                    }

                    long deadline = System.currentTimeMillis() + WRITE_TIMEOUT_MS;
                    while (!writeCompleted) {
                        long remaining = deadline - System.currentTimeMillis();
                        if (remaining <= 0) {
                            error = "UART write confirmation timeout at offset " + offset;
                            return false;
                        }
                        WRITE_LOCK.wait(remaining);
                    }
                    if (writeStatus != BluetoothGatt.GATT_SUCCESS) {
                        error = "UART write failed at offset " + offset
                            + ", status=" + writeStatus;
                        return false;
                    }
                }
            }
            return true;
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            error = "UART write was interrupted";
            return false;
        } catch (Exception exception) {
            Log.e(TAG, "Write failed", exception);
            error = exception.toString();
            return false;
        }
    }

    public static synchronized void disconnect() {
        BluetoothGatt current = gatt;
        gatt = null;
        writeCharacteristic = null;
        state = STATE_IDLE;
        if (current != null) {
            try {
                current.disconnect();
                current.close();
            } catch (Exception exception) {
                Log.w(TAG, "Disconnect failed", exception);
            }
        }
    }

    private static void fail(String message) {
        error = message == null ? "Unknown BLE error" : message;
        state = STATE_FAILED;
        Log.e(TAG, error);
    }

    private static BluetoothGattCharacteristic findWriteCharacteristic(
        BluetoothGatt currentGatt
    ) {
        for (BluetoothGattService service : currentGatt.getServices()) {
            for (BluetoothGattCharacteristic characteristic
                : service.getCharacteristics()) {
                if (WRITE_UUID.equals(characteristic.getUuid())) {
                    return characteristic;
                }
            }
        }
        return null;
    }

    private static final BluetoothGattCallback CALLBACK =
        new BluetoothGattCallback() {
            @Override
            public void onConnectionStateChange(
                BluetoothGatt currentGatt,
                int status,
                int newState
            ) {
                Log.i(
                    TAG,
                    "Connection state: status=" + status + ", state=" + newState
                );
                if (status == BluetoothGatt.GATT_SUCCESS
                    && newState == BluetoothProfile.STATE_CONNECTED) {
                    state = STATE_DISCOVERING;
                    if (!currentGatt.discoverServices()) {
                        fail("Could not start service discovery");
                    }
                    return;
                }
                if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                    if (state != STATE_IDLE) {
                        fail("Bluetooth device disconnected, status=" + status);
                    }
                    try {
                        currentGatt.close();
                    } catch (Exception ignored) {
                    }
                }
            }

            @Override
            public void onServicesDiscovered(BluetoothGatt currentGatt, int status) {
                Log.i(TAG, "Services discovered: status=" + status);
                if (status != BluetoothGatt.GATT_SUCCESS) {
                    fail("Service discovery failed, status=" + status);
                    return;
                }
                BluetoothGattCharacteristic characteristic =
                    findWriteCharacteristic(currentGatt);
                if (characteristic == null) {
                    fail("UART characteristic FFE1 was not found");
                    return;
                }
                int properties = characteristic.getProperties();
                Log.i(TAG, "FFE1 properties=0x" + Integer.toHexString(properties));
                if ((properties & BluetoothGattCharacteristic.PROPERTY_WRITE) == 0) {
                    fail("UART characteristic FFE1 does not support confirmed writes");
                    return;
                }
                writeCharacteristic = characteristic;
                state = STATE_CONNECTED;
                Log.i(TAG, "GATT connection is ready");
            }

            @Override
            public void onCharacteristicWrite(
                BluetoothGatt currentGatt,
                BluetoothGattCharacteristic characteristic,
                int status
            ) {
                Log.i(TAG, "Characteristic write status=" + status);
                synchronized (WRITE_LOCK) {
                    writeStatus = status;
                    writeCompleted = true;
                    WRITE_LOCK.notifyAll();
                }
            }
        };
}
