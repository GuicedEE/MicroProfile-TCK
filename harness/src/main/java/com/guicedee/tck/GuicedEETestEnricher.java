package com.guicedee.tck;

import com.guicedee.client.IGuiceContext;
import com.google.inject.Injector;
import java.lang.reflect.Method;
import org.jboss.arquillian.test.spi.TestEnricher;

public final class GuicedEETestEnricher implements TestEnricher {
    public void enrich(Object testCase) {
        if (GuicedEEContainer.deployed) IGuiceContext.get(Injector.class).injectMembers(testCase);
    }
    public Object[] resolve(Method method) { return new Object[method.getParameterCount()]; }
}
