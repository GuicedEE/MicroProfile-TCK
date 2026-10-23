package com.guicedee.tck;

import com.guicedee.client.IGuiceContext;
import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.jboss.arquillian.container.spi.client.container.*;
import org.jboss.arquillian.container.spi.client.protocol.ProtocolDescription;
import org.jboss.arquillian.container.spi.client.protocol.metadata.*;
import org.jboss.shrinkwrap.api.Archive;
import org.jboss.shrinkwrap.api.exporter.ExplodedExporter;
import org.jboss.shrinkwrap.descriptor.api.Descriptor;

/** Diagnostic embedded adapter. It does not substitute CDI, REST or other implementations. */
public final class GuicedEEContainer implements DeployableContainer<GuicedEEConfiguration> {
    private GuicedEEConfiguration configuration;
    private ClassLoader originalLoader;
    private URLClassLoader deploymentLoader;
    private boolean bootAttempted;
    private boolean used;
    static volatile boolean deployed;

    public Class<GuicedEEConfiguration> getConfigurationClass() { return GuicedEEConfiguration.class; }
    public void setup(GuicedEEConfiguration configuration) { this.configuration = configuration; }
    public void start() { }
    public void stop() throws LifecycleException {
        if (bootAttempted) {
            try { IGuiceContext.instance().destroy(); }
            catch (RuntimeException failure) { throw new LifecycleException("GuicedEE shutdown failed", failure); }
            finally { bootAttempted = false; }
        }
    }
    public ProtocolDescription getDefaultProtocol() { return new ProtocolDescription("Local"); }
    public ProtocolMetaData deploy(Archive<?> archive) throws DeploymentException {
        if (used) throw new DeploymentException("HARNESS-ISOLATION: GuicedEE shutdown is terminal; multiple deployments require separate runtime processes");
        used = true;
        if (!archive.getName().endsWith(".war") && !archive.getName().endsWith(".jar"))
            throw new DeploymentException("HARNESS-ARCHIVE: unsupported archive type " + archive.getName());
        try {
            Path base = Path.of("target", "deployments").toAbsolutePath();
            Files.createDirectories(base);
            Path directory = Files.createTempDirectory(base, "deployment-");
            Path exported = archive.as(ExplodedExporter.class).exportExploded(directory.toFile()).toPath();
            List<URL> urls = new ArrayList<>();
            urls.add(exported.toUri().toURL());
            if (Files.isDirectory(exported.resolve("WEB-INF/classes"))) urls.add(exported.resolve("WEB-INF/classes").toUri().toURL());
            if (Files.isDirectory(exported.resolve("WEB-INF/lib"))) {
                try (var files = Files.list(exported.resolve("WEB-INF/lib"))) {
                    for (Path jar : files.filter(p -> p.toString().endsWith(".jar")).sorted().toList()) urls.add(jar.toUri().toURL());
                }
            }
            originalLoader = Thread.currentThread().getContextClassLoader();
            deploymentLoader = new URLClassLoader(urls.toArray(URL[]::new), originalLoader);
            Thread.currentThread().setContextClassLoader(deploymentLoader);
            System.setProperty("HTTP_HOST", configuration.getHost());
            System.setProperty("HTTP_PORT", Integer.toString(configuration.getPort()));
            System.setProperty("HTTPS_ENABLED", "false");
            var context = IGuiceContext.instance();
            context.getConfig().setServiceLoadWithClassPath(true).setClasspathScanning(true)
                .setAnnotationScanning(true).setMethodInfo(true).setFieldInfo(true);
            bootAttempted = true;
            context.inject();
            context.getLoadingFinished().toCompletionStage().toCompletableFuture().get(30, TimeUnit.SECONDS);
            deployed = true;
            return new ProtocolMetaData().addContext(new HTTPContext(configuration.getHost(), configuration.getPort())
                .add(new Servlet("GuicedEE", "/")));
        } catch (Exception failure) {
            throw new DeploymentException("GuicedEE deployment failed for " + archive.getName(), failure);
        }
    }
    public void undeploy(Archive<?> archive) throws DeploymentException {
        deployed = false;
        try { stop(); }
        catch (LifecycleException failure) { throw new DeploymentException("GuicedEE undeployment failed", failure); }
        finally {
            if (originalLoader != null) Thread.currentThread().setContextClassLoader(originalLoader);
            if (deploymentLoader != null) try { deploymentLoader.close(); } catch (IOException ignored) { }
        }
    }
    public void deploy(Descriptor descriptor) throws DeploymentException {
        throw new DeploymentException("HARNESS-DESCRIPTOR: standalone descriptor deployment is unsupported");
    }
    public void undeploy(Descriptor descriptor) { }
}
