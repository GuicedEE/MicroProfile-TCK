package com.guicedee.tck;

import java.util.ServiceLoader;
import org.eclipse.microprofile.reactive.streams.operators.spi.ReactiveStreamsEngine;
import org.eclipse.microprofile.reactive.streams.operators.tck.ReactiveStreamsTck;
import org.reactivestreams.tck.TestEnvironment;

/** Executes the upstream factory without disabling any generated verification. */
public final class ReactiveStreamsVerificationTest extends ReactiveStreamsTck<ReactiveStreamsEngine> {
    public ReactiveStreamsVerificationTest() { super(new TestEnvironment()); }
    protected ReactiveStreamsEngine createEngine() {
        return ServiceLoader.load(ReactiveStreamsEngine.class).findFirst()
            .orElseThrow(() -> new IllegalStateException("No ReactiveStreamsEngine supplied by the GuicedEE runtime"));
    }
}
