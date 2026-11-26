package com.devicemanager;

import android.app.UiAutomation;
import android.graphics.Bitmap;
import android.os.HandlerThread;
import android.os.Looper;
import android.util.Base64;
import android.view.accessibility.AccessibilityNodeInfo;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Constructor;
import java.nio.charset.StandardCharsets;

/**
 * Minimal resident Android `app_process` server for fast UI hierarchy dumps.
 *
 * Keeps a single `UiAutomation` connection alive and responds to each `DUMP`
 * line on stdin with the current `<hierarchy>` XML without `waitForIdle`.
 */
public final class UiDumpServer {
    public static void main(String[] args) throws Exception {
        if (Looper.getMainLooper() == null) {
            Looper.prepareMainLooper();
        }
        HandlerThread handlerThread = new HandlerThread("UiDumpServer");
        handlerThread.start();

        Class<?> connClass = Class.forName("android.app.UiAutomationConnection");
        Object connection = connClass.getDeclaredConstructor().newInstance();
        Class<?> iConnClass = Class.forName("android.app.IUiAutomationConnection");
        Constructor<UiAutomation> ctor = UiAutomation.class.getDeclaredConstructor(
            Looper.class,
            iConnClass
        );
        UiAutomation automation = ctor.newInstance(handlerThread.getLooper(), connection);
        UiAutomation.class.getMethod("connect").invoke(automation);

        try (BufferedReader reader = new BufferedReader(
            new InputStreamReader(System.in, StandardCharsets.UTF_8)
        )) {
            String line;
            while ((line = reader.readLine()) != null) {
                if ("QUIT".equalsIgnoreCase(line.trim())) {
                    break;
                }
                if ("DUMP".equalsIgnoreCase(line.trim())) {
                    AccessibilityNodeInfo root = automation.getRootInActiveWindow();
                    StringBuilder sb = new StringBuilder();
                    sb.append("<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>");
                    sb.append("<hierarchy rotation=\"0\">");
                    if (root != null) {
                        serializeNode(root, sb, 0);
                        root.recycle();
                    }
                    sb.append("</hierarchy>\n");
                    System.out.print(sb.toString());
                    System.out.flush();
                } else if (
                    "SCREENSHOT".equalsIgnoreCase(line.trim())
                    || "SCREENSHOT_JPEG".equalsIgnoreCase(line.trim())
                ) {
                    boolean useJpeg = "SCREENSHOT_JPEG".equalsIgnoreCase(line.trim());
                    Bitmap bmp = automation.takeScreenshot();
                    if (bmp == null) {
                        System.out.print("IMG_ERR\n");
                    } else {
                        ByteArrayOutputStream baos = new ByteArrayOutputStream();
                        if (useJpeg) {
                            bmp.compress(Bitmap.CompressFormat.JPEG, 85, baos);
                        } else {
                            bmp.compress(Bitmap.CompressFormat.PNG, 100, baos);
                        }
                        bmp.recycle();
                        String b64 = Base64.encodeToString(
                            baos.toByteArray(),
                            Base64.NO_WRAP
                        );
                        System.out.print("IMG_BEGIN:");
                        System.out.print(b64);
                        System.out.print(":IMG_END\n");
                    }
                    System.out.flush();
                } else if (line.trim().toUpperCase().startsWith("SCREENSHOT_FILE ")) {
                    String path = line.trim().substring("SCREENSHOT_FILE ".length()).trim();
                    Bitmap bmp = automation.takeScreenshot();
                    if (bmp == null || path.isEmpty()) {
                        System.out.print("FILE_ERR\n");
                    } else {
                        try (FileOutputStream fos = new FileOutputStream(path)) {
                            bmp.compress(Bitmap.CompressFormat.JPEG, 85, fos);
                            System.out.print("FILE_OK\n");
                        } catch (Exception e) {
                            System.out.print("FILE_ERR\n");
                        } finally {
                            bmp.recycle();
                        }
                    }
                    System.out.flush();
                }
            }
        } finally {
            UiAutomation.class.getMethod("disconnect").invoke(automation);
            handlerThread.quitSafely();
        }
    }

    private static void serializeNode(
        AccessibilityNodeInfo node,
        StringBuilder sb,
        int index
    ) {
        android.graphics.Rect bounds = new android.graphics.Rect();
        node.getBoundsInScreen(bounds);
        sb.append("<node index=\"").append(index).append("\"");
        sb.append(" text=\"").append(escapeXml(node.getText())).append("\"");
        sb.append(" resource-id=\"").append(escapeXml(node.getViewIdResourceName())).append("\"");
        sb.append(" class=\"").append(escapeXml(node.getClassName())).append("\"");
        sb.append(" package=\"").append(escapeXml(node.getPackageName())).append("\"");
        sb.append(" content-desc=\"").append(escapeXml(node.getContentDescription())).append("\"");
        sb.append(" clickable=\"").append(node.isClickable()).append("\"");
        sb.append(" enabled=\"").append(node.isEnabled()).append("\"");
        sb.append(" bounds=\"[")
            .append(bounds.left).append(",").append(bounds.top)
            .append("][")
            .append(bounds.right).append(",").append(bounds.bottom)
            .append("]\"");

        int childCount = node.getChildCount();
        if (childCount == 0) {
            sb.append(" />");
            return;
        }
        sb.append(">");
        for (int i = 0; i < childCount; i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                serializeNode(child, sb, i);
                child.recycle();
            }
        }
        sb.append("</node>");
    }

    private static String escapeXml(CharSequence value) {
        if (value == null) {
            return "";
        }
        return value.toString()
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
            .replace("'", "&apos;");
    }
}
