package com.xxuniversity.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.xxuniversity.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
}
