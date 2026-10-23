package com.guicedee.tck.porting;

import jakarta.el.ELContext;
import jakarta.el.ExpressionFactory;
import jakarta.el.StandardELContext;
import jakarta.enterprise.inject.spi.BeanManager;
import org.jboss.cdi.tck.spi.EL;

/** Uses only the supplied runtime's EL factory and CDI resolver, without adding an EL provider. */
@SuppressWarnings({"removal", "unchecked"})
public final class GuicedEEEL implements EL {
    private ExpressionFactory factory(BeanManager manager) {
        return manager.wrapExpressionFactory(ExpressionFactory.newInstance());
    }
    @Override public ELContext createELContext(BeanManager manager) {
        var context = new StandardELContext(factory(manager));
        context.addELResolver(manager.getELResolver());
        return context;
    }
    @Override public <T> T evaluateValueExpression(BeanManager manager, String expression, Class<T> expectedType) {
        var context = createELContext(manager);
        return (T) factory(manager).createValueExpression(context, expression, expectedType).getValue(context);
    }
    @Override public <T> T evaluateMethodExpression(BeanManager manager, String expression, Class<T> expectedType,
                                                  Class<?>[] parameterTypes, Object[] parameters) {
        var context = createELContext(manager);
        return (T) factory(manager).createMethodExpression(context, expression, expectedType, parameterTypes).invoke(context, parameters);
    }
}
