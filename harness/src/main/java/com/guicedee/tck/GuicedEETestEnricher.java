package com.guicedee.tck;

import com.guicedee.client.IGuiceContext;
import com.google.inject.Injector;
import java.lang.reflect.Method;
import java.lang.reflect.Type;
import java.lang.annotation.Annotation;
import java.util.HashSet;
import java.util.Set;
import jakarta.enterprise.inject.Default;
import jakarta.enterprise.inject.spi.*;
import org.jboss.arquillian.test.spi.TestEnricher;

public final class GuicedEETestEnricher implements TestEnricher {
    public void enrich(Object testCase) {
        if (GuicedEEContainer.deployed) IGuiceContext.get(Injector.class).injectMembers(testCase);
    }
    public Object[] resolve(Method method) {
        var values = new Object[method.getParameterCount()];
        if (!GuicedEEContainer.deployed || !Boolean.getBoolean("tck.cdi.parameters") || values.length == 0) return values;
        var manager = CDI.current().getBeanManager();
        return resolveCdiParameters(method, manager);
    }
    static Object[] resolveCdiParameters(Method method, BeanContainer manager) {
        var values = new Object[method.getParameterCount()];
        for (int i = 0; i < values.length; i++) {
            Type type = method.getGenericParameterTypes()[i];
            Set<Annotation> qualifiers = new HashSet<>();
            for (var annotation : method.getParameterAnnotations()[i]) {
                if (manager.isQualifier(annotation.annotationType())) qualifiers.add(annotation);
            }
            if (qualifiers.isEmpty()) qualifiers.add(Default.Literal.INSTANCE);
            var beans = manager.getBeans(type, qualifiers.toArray(Annotation[]::new));
            var bean = manager.resolve(beans);
            if (bean == null) throw new jakarta.enterprise.inject.UnsatisfiedResolutionException("No CDI bean for test parameter " + type);
            values[i] = manager.getReference(bean, type, manager.createCreationalContext(bean));
        }
        return values;
    }
}
