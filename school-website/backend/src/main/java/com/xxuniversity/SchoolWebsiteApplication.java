package com.xxuniversity;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@MapperScan("com.xxuniversity.mapper")
@EnableCaching
@EnableAsync
public class SchoolWebsiteApplication {

    public static void main(String[] args) {
        SpringApplication.run(SchoolWebsiteApplication.class, args);
    }

}
