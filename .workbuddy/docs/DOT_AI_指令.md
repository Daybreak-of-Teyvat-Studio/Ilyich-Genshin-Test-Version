我要你阅读文件DOT_HOI4_Modding_Skills，对BUG进行修复，而不是偷懒把有问题的代码注释掉。

对照error日志，将所有Event、focus、ideas decison effect modifier trigger、on action的错误效果改成正确效果，不知道怎么修正的就用#注销，并#备注原因

优化所有采用create_country_leader = { create_field_marshal = { create_corps_commander = { create_navy_leader = {的国家，将之改为Daybreak of Teyvat Beta Version\common\characters中的形式，并为history countries添加招募代码。
大头像large可以用原来的图片，找不到小头像small的一律使用这个图片small="gfx/interface/cabinet/Ying.dds"

Missing icon for focus 的focus就为之添加icon = GFX_goal_unknown #。
Missing icon shine for focus的focus就按下面的方案将图片路径复制一遍。就像这样，普通icon和shine icon用的是同一张图片。你只需要在没有shine icon的普通icon的定位下面加一条shine icon的代码即可。
SpriteType = {
    name = "GFX_FOD_Press_the_Fatui"
    texturefile = "gfx/interface/goals/FOD/GFX_FOD_Press_the_Fatui.png"
}

SpriteType = {
    name = "GFX_FOD_Press_the_Fatui_shine"
    texturefile = "gfx/interface/goals/FOD/GFX_FOD_Press_the_Fatui.png"
    effectFile = "gfx/FX/buttonstate.lua"
    animation = {
        animationmaskfile = "gfx/interface/goals/FOD/GFX_FOD_Press_the_Fatui.png"
        animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
        animationrotation = -90.0
        animationlooping = no
        animationtime = 0.75
        animationdelay = 0
        animationblendmode = "add"
        animationtype = "scrolling"
        animationrotationoffset = { x = 0.0 y = 0.0 }
        animationtexturescale = { x = 1.0 y = 1.0 }
    }
    animation = {
        animationmaskfile = "GFX_FOD_Press_the_Fatui.png"
        animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
        animationrotation = 90.0
        animationlooping = no
        animationtime = 0.75
        animationdelay = 0
        animationblendmode = "add"
        animationtype = "scrolling"
        animationrotationoffset = { x = 0.0 y = 0.0 }
        animationtexturescale = { x = 1.0 y = 1.0 }
    }
    legacy_lazy_load = no
}