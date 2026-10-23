package com.guicedee.tck;

import org.jboss.arquillian.container.spi.client.container.ContainerConfiguration;

public final class GuicedEEConfiguration implements ContainerConfiguration {
    private String host = "127.0.0.1";
    private int port = Integer.getInteger("tck.http.port", 18080);
    public String getHost() { return host; }
    public void setHost(String host) { this.host = host; }
    public int getPort() { return port; }
    public void setPort(int port) { this.port = Integer.getInteger("tck.http.port", port); }
    public void validate() {
        if (!"127.0.0.1".equals(host) || port < 1024 || port > 65535)
            throw new IllegalArgumentException("TCK servers must bind to loopback on an unprivileged port");
    }
}
