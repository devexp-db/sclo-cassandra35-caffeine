%{?scl:%scl_package caffeine}
%{!?scl:%global pkg_name %{name}}

# depend on guava 20.0 RHBZ#1307246
%bcond_with guava
%bcond_with jcache

Name:		%{?scl_prefix}caffeine
Version:	2.3.5
Release:	2%{?dist}
Summary:	High performance, near optimal caching library based on Java 8
License:	ASL 2.0
URL:		https://github.com/ben-manes/%{pkg_name}
Source0:	https://github.com/ben-manes/%{pkg_name}/archive/v%{version}/%{pkg_name}-%{version}.tar.gz
Source1:	https://repo1.maven.org/maven2/com/github/ben-manes/%{pkg_name}/%{pkg_name}/%{version}/%{pkg_name}-%{version}.pom
Source2:	%{pkg_name}-gen.pom
%if %{with guava}
Source3:        http://repo1.maven.org/maven2/com/github/ben-manes/%{pkg_name}/guava/%{version}/guava-%{version}.pom
%endif
%if %{with jcache}
Source4:        http://repo1.maven.org/maven2/com/github/ben-manes/%{pkg_name}/jcache/%{version}/jcache-%{version}.pom
%endif

BuildArch:	noarch

# nasty hack TODO
BuildRequires:	java-1.8.0-openjdk-devel
Requires:	java-1.8.0-openjdk-devel
BuildRequires:	%{?scl_prefix_maven}maven-local
BuildRequires:	%{?scl_prefix_maven}jsr-305
BuildRequires:	%{?scl_prefix_maven}apache-commons-lang3
BuildRequires:	%{?scl_prefix_maven}exec-maven-plugin
BuildRequires:	%{?scl_prefix_maven}maven-plugin-bundle
BuildRequires:	%{?scl_prefix}guava
BuildRequires:	%{?scl_prefix}javapoet
%{?scl:Requires: %scl_runtime}

%description
A Cache is similar to ConcurrentMap, but not quite the same. The most
fundamental difference is that a ConcurrentMap persists all elements that are
added to it until they are explicitly removed. A Cache on the other hand is
generally configured to evict entries automatically, in order to constrain its
memory footprint. In some cases a LoadingCache or AsyncLoadingCache can be
useful even if it doesn't evict entries, due to its automatic cache loading.

Caffeine provide flexible construction to create a cache with a combination
of the following features:
automatic loading of entries into the cache, optionally asynchronously
size-based eviction when a maximum is exceeded based on frequency and recency
time-based expiration of entries, measured since last access or last write
asynchronously refresh when the first stale request for an entry occurs
keys automatically wrapped in weak references
values automatically wrapped in weak or soft references
notification of evicted (or otherwise removed) entries
writes propagated to an external resource
accumulation of cache access statistics

%if %{with guava}
%package guava
Summary:	Caffeine Guava extension

%description guava
An adapter to expose a Caffeine cache through the Guava interfaces.
%endif
%if %{with jcache}
%package jcache
Summary:	Caffeine JSR-107 JCache extension

%description jcache
An adapter to expose a Caffeine cache through the JCache interfaces.
%endif

%package javadoc
Summary:	Javadoc for %{name}

%description javadoc
This package contains the API documentation for %{name}.

%prep
%setup -q -n %{pkg_name}-%{version}

find -name "*.jar" -print -delete

# This is a dummy POM added just to ease building in the RPM platforms
cat > pom.xml << EOF
<?xml version="1.0" encoding="UTF-8"?>
<project
  xmlns="http://maven.apache.org/POM/4.0.0"
  xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <modelVersion>4.0.0</modelVersion>
  <groupId>com.github.ben-manes.caffeine</groupId>
  <artifactId>%{pkg_name}-parent</artifactId>
  <version>%{version}</version>
  <packaging>pom</packaging>
  <name>Caffeine Parent</name>
  <modules>
    <module>%{pkg_name}</module>
    <!-- module>simulator</module -->
    <!-- module>examples/write-behind-rxjava</module -->
  </modules>
</project>
EOF

cp -p %{SOURCE1} %{pkg_name}/pom.xml
cp -p %{SOURCE2} %{pkg_name}/gen.pom

%if %{with guava}
cp -p %{SOURCE3} guava/pom.xml
%endif
%if %{with jcache}
cp -p %{SOURCE4} jcache/pom.xml
%endif

%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
(
 for p in guava \
  jcache; do
 %if %{with $p}
 %pom_xpath_inject "pom:project/pom:modules" "<module>${p}</module>"
 %pom_xpath_inject "pom:project" "
 <properties>
     <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
 </properties>" ${p}
 %pom_xpath_inject "pom:project" "
   <build>
     <pluginManagement>
       <plugins>
         <plugin>
           <groupId>org.apache.maven.plugins</groupId>
           <artifactId>maven-compiler-plugin</artifactId>
           <version>2.3.2</version>
           <configuration>
             <source>1.8</source>
             <target>1.8</target>
             <showDeprecation>true</showDeprecation>
           </configuration>
         </plugin>
       </plugins>
     </pluginManagement>
   </build>" ${p}

 %pom_xpath_set "pom:project/pom:name" "Caffeine ${p} extension" ${p}
 %pom_xpath_inject "pom:project" "<packaging>bundle</packaging>" ${p}
 %pom_add_plugin org.apache.felix:maven-bundle-plugin ${p} "
 <extensions>true</extensions>
 <configuration>
   <instructions>
     <Bundle-SymbolicName>\${project.groupId}.${p}</Bundle-SymbolicName>
     <Bundle-Name>\${project.groupId}.${p}</Bundle-Name>
     <Bundle-Version>\${project.version}</Bundle-Version>
   </instructions>
 </configuration>
 <executions>
   <execution>
     <id>bundle-manifest</id>
     <phase>process-classes</phase>
     <goals>
       <goal>manifest</goal>
     </goals>
   </execution>
 </executions>"
 %pom_remove_dep com.google.errorprone:error_prone_annotations ${p}
 %endif
 echo hello
done
)

%pom_xpath_inject "pom:project" "<properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>" %{pkg_name}

%pom_xpath_inject "pom:project" "
  <build>
    <pluginManagement>
      <plugins>
          <plugin>
          <groupId>org.apache.maven.plugins</groupId>
          <artifactId>maven-compiler-plugin</artifactId>
          <version>2.3.2</version>
          <configuration>
            <source>1.8</source>
            <target>1.8</target>
            <showDeprecation>true</showDeprecation>
          </configuration>
        </plugin>
      </plugins>
    </pluginManagement>
  </build>" %{pkg_name}

%pom_xpath_inject "pom:project" "<packaging>bundle</packaging>" %{pkg_name}
%pom_add_plugin org.apache.felix:maven-bundle-plugin %{pkg_name} "
    <extensions>true</extensions>
      <configuration>
        <excludeDependencies>true</excludeDependencies>
        <instructions>
          <Bundle-SymbolicName>com.github.ben-manes.caffeine</Bundle-SymbolicName>
          <Bundle-Name>com.github.ben-manes.caffeine</Bundle-Name>
          <Bundle-Version>\${project.version}</Bundle-Version>
        </instructions>
      </configuration>
    <executions>
   <execution>
     <id>bundle-manifest</id>
     <phase>process-classes</phase>
     <goals>
       <goal>manifest</goal>
     </goals>
   </execution>
 </executions>"

# remove missing dependency
%pom_remove_dep com.google.errorprone:error_prone_annotations %{pkg_name}

%if %{with jcache}
# Use open source JSR-107 apis
%pom_change_dep javax.cache:cache-api org.apache.geronimo.specs:geronimo-jcache_1.0_spec jcache
%endif

%mvn_package :%{pkg_name}-parent __noinstall
%{?scl:EOF}

%build
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
(
 cd %{pkg_name}
 for class in com.github.benmanes.caffeine.cache.LocalCacheFactoryGenerator \
         com.github.benmanes.caffeine.cache.NodeFactoryGenerator; do
   xmvn -B --offline -f gen.pom compile exec:java -Dexec.mainClass=$class -Dexec.args=src/main/java
 done
)

# tests are skipped due to missing dependencies
%mvn_build -sf
%{?scl:EOF}

%install
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
%mvn_install
%{?scl:EOF}

%files -f .mfiles-%{pkg_name}
%doc README.md
%license LICENSE

%if %{with guava}
%files guava -f .mfiles-guava
%endif

%if %{with jcache}
%files jcache -f .mfiles-jcache
%endif

%files javadoc -f .mfiles-javadoc
%license LICENSE

%changelog
* Tue Nov 29 2016 Tomas Repik <trepik@redhat.com> - 2.3.5-2
- scl conversion

* Mon Nov 21 2016 Tomas Repik <trepik@redhat.com> - 2.3.5-1
- initial package
