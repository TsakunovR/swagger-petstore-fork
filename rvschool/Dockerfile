FROM swaggerapi/petstore3@sha256:97e5aa178dd4d160af9e31a900a685a943cd715cab7ba6ca6377fe976e95d1cf AS original
FROM eclipse-temurin:17-jdk@sha256:7a0b2bc7e1372bb05ee361fb79e8a9e822df47343b8716253b3bbaa75060653e AS build
WORKDIR /build
COPY --from=original /swagger-petstore/webapps/ROOT.war /build/ROOT.war
RUN jar xf ROOT.war
COPY rvschool/PetController.original.java /original-src/io/swagger/petstore/controller/PetController.java
RUN javap -classpath WEB-INF/classes -c -p io.swagger.petstore.controller.PetController > original.javap.txt \
    && javac --release 17 -cp 'WEB-INF/classes:WEB-INF/lib/*' -d original-compiled /original-src/io/swagger/petstore/controller/PetController.java \
    && javap -classpath original-compiled -c -p io.swagger.petstore.controller.PetController > recompiled.javap.txt
COPY src/main/java/io/swagger/petstore/controller/PetController.java /src/io/swagger/petstore/controller/PetController.java
RUN javac --release 17 -cp 'WEB-INF/classes:WEB-INF/lib/*' -d WEB-INF/classes /src/io/swagger/petstore/controller/PetController.java \
    && javap -classpath WEB-INF/classes -c -p io.swagger.petstore.controller.PetController > patched.javap.txt \
    && jar uf ROOT.war WEB-INF/classes/io/swagger/petstore/controller/PetController.class
FROM original AS runtime
COPY --from=build /build/ROOT.war /swagger-petstore/webapps/ROOT.war
COPY --from=build /build/original.javap.txt /build/recompiled.javap.txt /build/patched.javap.txt /opt/petstore-build-evidence/
COPY src/main/java/io/swagger/petstore/controller/PetController.java /opt/petstore-source/PetController.java
COPY rvschool/UPSTREAM_COMMIT /opt/petstore-source/UPSTREAM_COMMIT
COPY src/main/resources/openapi.yaml /swagger-petstore/openapi.yaml
