package com.guicedee.tck.porting;

import java.io.NotSerializableException;
import java.util.List;
import org.jboss.cdi.tck.impl.PropertiesBasedConfigurationBuilder;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Harness checks, outside the official suite's org.jboss.cdi.tck test packages. */
public class PortingContractTest {
    @Test public void officialConfigurationFindsAllPortingHooks() {
        for (boolean deploymentPhase : new boolean[] { false, true }) {
            var configuration = new PropertiesBasedConfigurationBuilder().init(deploymentPhase).getConfiguration();
            Assert.assertTrue(configuration.getCdiLiteMode());
            Assert.assertTrue(configuration.getBeans() instanceof GuicedEEBeans);
            Assert.assertTrue(configuration.getContexts() instanceof GuicedEEContexts);
            Assert.assertTrue(configuration.getEl() instanceof GuicedEEEL);
        }
    }
    @Test public void serializationRoundTrip() throws Exception {
        var beans = new GuicedEEBeans();
        Assert.assertEquals(beans.activate(beans.passivate(List.of("fixture"))), List.of("fixture"));
    }
    @Test(expectedExceptions = NotSerializableException.class)
    public void serializationDoesNotSubstituteForUnsupportedObjects() throws Exception {
        new GuicedEEBeans().passivate(new Object());
    }
    @Test(expectedExceptions = UnsupportedOperationException.class, expectedExceptionsMessageRegExp = "HARNESS-CDI-PROXY:.*")
    public void proxyIntrospectionCannotPretendToPass() { new GuicedEEBeans().isProxy(new Object()); }
    @Test public void lifecycleOperationsCannotPretendToSucceed() {
        var contexts = new GuicedEEContexts();
        Assert.expectThrows(UnsupportedOperationException.class, () -> contexts.setActive(null));
        Assert.expectThrows(UnsupportedOperationException.class, () -> contexts.setInactive(null));
        Assert.expectThrows(UnsupportedOperationException.class, () -> contexts.destroyContext(null));
    }
}
