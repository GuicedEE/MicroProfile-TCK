package com.guicedee.tck;

import jakarta.enterprise.inject.Default;
import jakarta.enterprise.inject.Instance;
import jakarta.enterprise.inject.spi.*;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.lang.reflect.InvocationHandler;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CdiParameterEnrichmentTest {
    void fixture(Instance<String> value) { }

    @SuppressWarnings("unchecked")
    static <T> T proxy(Class<T> type, InvocationHandler handler) {
        return (T) Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type}, handler);
    }

    @Test void delegatesGenericInjectionPointInsteadOfSupplyingNull() throws Exception {
        Method method = getClass().getDeclaredMethod("fixture", Instance.class);
        Object expected = new Object();
        AtomicInteger calls = new AtomicInteger();
        Bean<?> bean = proxy(Bean.class, (p,m,a) -> {
            if (m.getName().equals("hashCode")) return 1;
            throw new UnsupportedOperationException(m.getName());
        });
        BeanContainer manager = proxy(BeanContainer.class, (p,m,a) -> switch(m.getName()) {
            case "getBeans" -> {
                assertEquals(method.getGenericParameterTypes()[0], a[0]);
                assertArrayEquals(new java.lang.annotation.Annotation[]{Default.Literal.INSTANCE}, (java.lang.annotation.Annotation[]) a[1]);
                yield Set.of(bean);
            }
            case "resolve" -> bean;
            case "createCreationalContext" -> null;
            case "getReference" -> {
                assertSame(bean, a[0]);
                assertEquals(method.getGenericParameterTypes()[0], a[1]);
                calls.incrementAndGet();
                yield expected;
            }
            default -> throw new UnsupportedOperationException(m.getName());
        });
        assertSame(expected, GuicedEETestEnricher.resolveCdiParameters(method, manager)[0]);
        assertEquals(1, calls.get());
    }

    @Test void unsupportedRuntimeApiIsNotConvertedToNull() throws Exception {
        BeanContainer manager = proxy(BeanContainer.class, (p,m,a) -> { throw new UnsupportedOperationException("runtime API missing"); });
        Method method = getClass().getDeclaredMethod("fixture", Instance.class);
        var failure = assertThrows(UnsupportedOperationException.class, () -> GuicedEETestEnricher.resolveCdiParameters(method, manager));
        assertEquals("runtime API missing", failure.getMessage());
    }

    @Test void unresolvedParameterFailsInsteadOfSupplyingNull() throws Exception {
        BeanContainer manager = proxy(BeanContainer.class, (p,m,a) -> switch(m.getName()) {
            case "getBeans" -> Set.of();
            case "resolve" -> null;
            default -> throw new UnsupportedOperationException(m.getName());
        });
        Method method = getClass().getDeclaredMethod("fixture", Instance.class);
        assertThrows(jakarta.enterprise.inject.UnsatisfiedResolutionException.class,
            () -> GuicedEETestEnricher.resolveCdiParameters(method, manager));
    }
}
