package com.guicedee.tck.porting;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.TreeSet;
import java.util.ArrayList;
import org.testng.xml.XmlSuite;
import org.testng.IMethodInterceptor;
import org.testng.TestNG;
import org.testng.xml.Parser;

/** Asks the pinned TestNG engine for the official selected methods, without invoking any test. */
public final class CdiSuiteDiscovery {
    public static void main(String[] args) throws Exception {
        var selected = new TreeSet<String>();
        var testng = new TestNG();
        var suites = new ArrayList<XmlSuite>();
        var source = Path.of(args[0]);
        if (Files.isDirectory(source)) {
            try (var paths = Files.list(source)) {
                for (var path : paths.filter(p -> p.toString().endsWith(".xml")).sorted().toList()) {
                    suites.addAll(new Parser(path.toString()).parseToList());
                }
            }
        } else { suites.addAll(new Parser(args[0]).parseToList()); }
        testng.setXmlSuites(suites);
        testng.setOutputDirectory(args[2]);
        testng.setUseDefaultListeners(false);
        testng.addListener((IMethodInterceptor) (methods, context) -> {
            for (var method : methods) {
                selected.add(method.getMethod().getTestClass().getName() + "#" + method.getMethod().getMethodName());
            }
            return List.of();
        });
        testng.run();
        if (selected.isEmpty()) throw new IllegalStateException("No official CDI Lite methods discovered");
        Files.write(Path.of(args[1]), selected);
    }
}
