package com.guicedee.tck;

import jakarta.enterprise.inject.build.compatible.spi.BuildCompatibleExtension;
import jakarta.enterprise.inject.build.compatible.spi.Enhancement;
import jakarta.enterprise.lang.model.declarations.ClassInfo;
import org.jboss.cdi.lang.model.tck.LangModelVerifier;

public final class LangModelExtension implements BuildCompatibleExtension {
    static int invocations;
    @Enhancement(types = LangModelVerifier.class)
    public void verify(ClassInfo model) {
        LangModelVerifier.verify(model);
        invocations++;
    }
}
