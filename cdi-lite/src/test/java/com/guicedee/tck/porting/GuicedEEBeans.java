package com.guicedee.tck.porting;

import java.io.*;
import org.jboss.cdi.tck.spi.Beans;

/** Diagnostic porting only: never invent proxy semantics for the runtime under test. */
public final class GuicedEEBeans implements Beans {
    @Override public boolean isProxy(Object instance) {
        throw new UnsupportedOperationException("HARNESS-CDI-PROXY: no verified GuicedEE CDI client-proxy introspection hook");
    }

    @Override public byte[] passivate(Object instance) throws IOException {
        var bytes = new ByteArrayOutputStream();
        try (var stream = new ObjectOutputStream(bytes)) { stream.writeObject(instance); }
        return bytes.toByteArray();
    }

    @Override public Object activate(byte[] bytes) throws IOException, ClassNotFoundException {
        try (var stream = new ObjectInputStream(new ByteArrayInputStream(bytes)) {
            @Override protected Class<?> resolveClass(ObjectStreamClass descriptor) throws IOException, ClassNotFoundException {
                try { return Class.forName(descriptor.getName(), false, Thread.currentThread().getContextClassLoader()); }
                catch (ClassNotFoundException missing) { return super.resolveClass(descriptor); }
            }
        }) { return stream.readObject(); }
    }
}
