package com.guicedee.tck;

import jakarta.enterprise.inject.build.compatible.spi.BuildCompatibleExtension;
import org.jboss.arquillian.container.test.api.Deployment;
import org.jboss.arquillian.testng.Arquillian;
import org.jboss.cdi.lang.model.tck.LangModelVerifier;
import org.jboss.shrinkwrap.api.ShrinkWrap;
import org.jboss.shrinkwrap.api.spec.WebArchive;
import org.jboss.shrinkwrap.api.asset.StringAsset;
import org.testng.Assert;
import org.testng.annotations.Test;

public final class LanguageModelVerificationTest extends Arquillian {
    @Deployment
    public static WebArchive deployment() {
        return ShrinkWrap.create(WebArchive.class, "language-model.war")
            .addClasses(LanguageModelVerificationTest.class, LangModelExtension.class)
            .addPackages(true, LangModelVerifier.class.getPackage())
            .addAsServiceProvider(BuildCompatibleExtension.class, LangModelExtension.class)
            .addAsWebInfResource(new StringAsset("<beans xmlns=\"https://jakarta.ee/xml/ns/jakartaee\" bean-discovery-mode=\"all\" version=\"4.0\"/>"), "beans.xml");
    }
    @Test
    public void officialLanguageModelVerifierWasInvoked() {
        Assert.assertEquals(LangModelExtension.invocations, 1,
            "The runtime must invoke the official verifier through its build-compatible extension lifecycle");
    }
}
