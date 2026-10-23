package com.guicedee.tck.porting;

import jakarta.enterprise.context.Dependent;
import jakarta.enterprise.context.RequestScoped;
import jakarta.enterprise.context.spi.Context;
import jakarta.enterprise.inject.spi.CDI;
import org.jboss.cdi.tck.spi.Contexts;

/** Context lookup delegates to the actual CDI provider; lifecycle gaps fail explicitly. */
public final class GuicedEEContexts implements Contexts<Context> {
    @Override public Context getRequestContext() {
        return CDI.current().getBeanManager().getContext(RequestScoped.class);
    }
    @Override public Context getDependentContext() {
        return CDI.current().getBeanManager().getContext(Dependent.class);
    }
    @Override public void setActive(Context context) { throw unsupported("setActive"); }
    @Override public void setInactive(Context context) { throw unsupported("setInactive"); }
    @Override public void destroyContext(Context context) { throw unsupported("destroyContext"); }
    private static UnsupportedOperationException unsupported(String operation) {
        return new UnsupportedOperationException("HARNESS-CDI-CONTEXT: no verified GuicedEE lifecycle hook for " + operation);
    }
}
