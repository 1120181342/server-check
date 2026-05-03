package com.xxuniversity.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;
import org.springframework.core.env.Profiles;
import springfox.documentation.builders.ApiInfoBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.*;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spi.service.contexts.SecurityContext;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

@Configuration
@EnableSwagger2
public class SwaggerConfig {

    @Bean
    public Docket api(Environment environment) {
        Profiles profiles = Profiles.of("dev", "test");
        boolean enableSwagger = environment.acceptsProfiles(profiles);

        return new Docket(DocumentationType.SWAGGER_2)
                .enable(enableSwagger)
                .apiInfo(apiInfo())
                .groupName("XX大学官网API_v1.0")
                .select()
                .apis(RequestHandlerSelectors.basePackage("com.xxuniversity.controller"))
                .paths(PathSelectors.any())
                .build()
                .securityContexts(securityContexts())
                .securitySchemes(securitySchemes())
                .globalOperationParameters(globalOperationParameters());
    }

    private ApiInfo apiInfo() {
        return new ApiInfoBuilder()
                .title("XX大学官网 - API文档")
                .description("XX大学官网后端服务RESTful API接口文档，支持与外部链接程序对接")
                .version("1.0.0")
                .contact(new Contact("XX大学信息化中心", "https://www.xxuniversity.edu.cn", "it@xxuniversity.edu.cn"))
                .license("Apache License 2.0")
                .licenseUrl("https://www.apache.org/licenses/LICENSE-2.0")
                .build();
    }

    private List<SecurityScheme> securitySchemes() {
        List<SecurityScheme> securitySchemes = new ArrayList<>();
        securitySchemes.add(new ApiKey("Authorization", "Authorization", "header"));
        return securitySchemes;
    }

    private List<SecurityContext> securityContexts() {
        List<SecurityContext> securityContexts = new ArrayList<>();
        securityContexts.add(SecurityContext.builder()
                .securityReferences(defaultAuth())
                .operationSelector(o -> o.requestMappingPattern().matches("^(?!auth).*$"))
                .build());
        return securityContexts;
    }

    private List<SecurityReference> defaultAuth() {
        AuthorizationScope authorizationScope = new AuthorizationScope("global", "accessEverything");
        AuthorizationScope[] authorizationScopes = new AuthorizationScope[1];
        authorizationScopes[0] = authorizationScope;
        return Arrays.asList(new SecurityReference("Authorization", authorizationScopes));
    }

    private List<springfox.documentation.service.Parameter> globalOperationParameters() {
        List<springfox.documentation.service.Parameter> parameters = new ArrayList<>();
        
        parameters.add(new ParameterBuilder()
                .name("Authorization")
                .description("JWT Token，格式：Bearer {token}")
                .modelRef(new springfox.documentation.schema.ModelRef("string"))
                .parameterType("header")
                .required(false)
                .build());
        
        return parameters;
    }
}
