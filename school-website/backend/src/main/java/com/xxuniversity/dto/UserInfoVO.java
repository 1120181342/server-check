package com.xxuniversity.dto;

import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
public class UserInfoVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    private String userId;

    private String username;

    private String realName;

    private String email;

    private String phone;

    private String avatar;

    private String gender;

    private String department;

    private String role;

    private LocalDateTime enrollDate;
}
