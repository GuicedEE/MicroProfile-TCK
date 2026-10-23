package com.guicedee.tck;

import com.google.inject.AbstractModule;
import com.google.inject.name.Names;
import com.guicedee.client.IGuiceContext;
import junit.framework.Test;
import junit.framework.TestSuite;
import org.atinject.tck.Tck;
import org.atinject.tck.auto.*;
import org.atinject.tck.auto.accessories.SpareTire;

public final class InjectionVerificationTest extends TestSuite {
    public static Test suite() {
        IGuiceContext.modules.add(new AbstractModule() {
            protected void configure() {
                bind(Car.class).to(Convertible.class);
                bind(Seat.class).annotatedWith(Drivers.class).to(DriversSeat.class);
                bind(Engine.class).to(V8Engine.class);
                bind(Tire.class).annotatedWith(Names.named("spare")).to(SpareTire.class);
                requestStaticInjection(Convertible.class, SpareTire.class);
            }
        });
        var context = IGuiceContext.instance();
        context.getConfig().setServiceLoadWithClassPath(true).setClasspathScanning(true).setAnnotationScanning(true);
        context.inject();
        return Tck.testsFor(IGuiceContext.get(Car.class), true, true);
    }
}
