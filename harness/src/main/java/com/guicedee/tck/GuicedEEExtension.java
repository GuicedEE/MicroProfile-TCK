package com.guicedee.tck;

import org.jboss.arquillian.core.spi.LoadableExtension;
import org.jboss.arquillian.container.spi.client.container.DeployableContainer;
import org.jboss.arquillian.test.spi.TestEnricher;

public final class GuicedEEExtension implements LoadableExtension {
    public void register(ExtensionBuilder builder) {
        builder.service(DeployableContainer.class, GuicedEEContainer.class);
        builder.service(TestEnricher.class, GuicedEETestEnricher.class);
    }
}
