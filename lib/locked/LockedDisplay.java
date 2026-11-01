import android.content.AttributionSource;
import android.content.Context;
import android.content.ContextWrapper;
import android.graphics.PixelFormat;
import android.hardware.display.VirtualDisplay;
import android.hardware.display.VirtualDisplayConfig;
import android.media.Image;
import android.media.ImageReader;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.Looper;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.concurrent.Executor;

/**
 * A display of a virtual device, made as the adb shell user. On Android 17 it has its own display group and power group,
 * so it keeps running while the phone is locked. It prints "display N" and keeps the display until the process ends.
 * Usage: app_process / LockedDisplay ASSOCIATION_ID W H DPI FLAGS(hex)
 */
public class LockedDisplay {
    public static void main(String[] args) throws Exception {
        int assoc = Integer.parseInt(args[0]);
        int w = Integer.parseInt(args[1]), h = Integer.parseInt(args[2]), dpi = Integer.parseInt(args[3]);
        int flags = (int) Long.parseLong(args[4], 16);
        Looper.prepareMainLooper();
        Class<?> at = Class.forName("android.app.ActivityThread");
        Constructor<?> c = at.getDeclaredConstructor();
        c.setAccessible(true);
        Object thread = c.newInstance();
        Field cur = at.getDeclaredField("sCurrentActivityThread");
        cur.setAccessible(true);
        cur.set(null, thread);
        Field sys = at.getDeclaredField("mSystemThread");
        sys.setAccessible(true);
        sys.setBoolean(thread, true);
        Method gsc = at.getDeclaredMethod("getSystemContext");
        gsc.setAccessible(true);
        Context system = (Context) gsc.invoke(thread);
        final AttributionSource source = new AttributionSource.Builder(2000).setPackageName("com.android.shell").build();
        Context shell = new ContextWrapper(system) {
            @Override public String getPackageName() { return "com.android.shell"; }
            @Override public String getOpPackageName() { return "com.android.shell"; }
            @Override public AttributionSource getAttributionSource() { return source; }
            @Override public Context getApplicationContext() { return this; }
        };
        IBinder b = (IBinder) Class.forName("android.os.ServiceManager").getMethod("getService", String.class).invoke(null, "virtualdevice");
        Class<?> ivdm = Class.forName("android.companion.virtual.IVirtualDeviceManager");
        Object svc = Class.forName("android.companion.virtual.IVirtualDeviceManager$Stub").getMethod("asInterface", IBinder.class).invoke(null, b);
        Class<?> vdmC = Class.forName("android.companion.virtual.VirtualDeviceManager");
        Constructor<?> vdmK = vdmC.getDeclaredConstructor(ivdm, Context.class);
        vdmK.setAccessible(true);
        Object vdm = vdmK.newInstance(svc, shell);
        Class<?> pb = Class.forName("android.companion.virtual.VirtualDeviceParams$Builder");
        Object builder = pb.getConstructor().newInstance();
        pb.getMethod("setName", String.class).invoke(builder, "meowtty");
        Object params = pb.getMethod("build").invoke(builder);
        Class<?> paramsC = Class.forName("android.companion.virtual.VirtualDeviceParams");
        Object device = vdmC.getMethod("createVirtualDevice", int.class, paramsC).invoke(vdm, assoc, params);
        System.out.println("device " + device.getClass().getMethod("getDeviceId").invoke(device));

        HandlerThread ht = new HandlerThread("frames");
        ht.start();
        ImageReader reader = ImageReader.newInstance(w, h, PixelFormat.RGBA_8888, 2);
        reader.setOnImageAvailableListener(r -> { Image i = r.acquireLatestImage(); if (i != null) i.close(); }, new Handler(ht.getLooper()));
        VirtualDisplayConfig cfg = new VirtualDisplayConfig.Builder("meowtty-vd", w, h, dpi).setSurface(reader.getSurface()).setFlags(flags).build();
        Executor ex = Runnable::run;
        Method cvd = device.getClass().getMethod("createVirtualDisplay", VirtualDisplayConfig.class, Executor.class, VirtualDisplay.Callback.class);
        VirtualDisplay vd = (VirtualDisplay) cvd.invoke(device, cfg, ex, null);
        System.out.println("display " + vd.getDisplay().getDisplayId());
        Looper.loop();
    }
}
