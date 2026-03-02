package com.pomodorotable.app;

import android.os.Bundle;
import android.util.Log;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import com.getcapacitor.BridgeActivity;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

public class MainActivity extends BridgeActivity {
	private static final String TAG = "PomodoroTable";
	private static final AtomicBoolean backendStarted = new AtomicBoolean(false);
	private static final ExecutorService backendExecutor = Executors.newSingleThreadExecutor();

	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		startEmbeddedBackend();
	}

	private void startEmbeddedBackend() {
		if (backendStarted.getAndSet(true)) {
			return;
		}

		backendExecutor.execute(() -> {
			try {
				if (!Python.isStarted()) {
					Python.start(new AndroidPlatform(getApplicationContext()));
				}

				Python python = Python.getInstance();
				PyObject module = python.getModule("mobile_server");
				module.callAttr("start_server", getFilesDir().getAbsolutePath());
			} catch (Exception ex) {
				Log.e(TAG, "Failed to start embedded FastAPI backend", ex);
			}
		});
	}
}
