#include <linux/gpio.h>
#include <stdalign.h>
#include <stdio.h>
#include <stdlib.h>

#define dump_ioctl(ident) printf("\"%s\":%lu,", #ident, ident)

#define dump_struct_info(ident) printf("\"%s\":{\"sizeof\":%lu,\"alignof\":%lu},", #ident, sizeof(struct ident), alignof(struct ident))

int main(void) {
    printf("{");

    dump_ioctl(GPIO_GET_CHIPINFO_IOCTL);
    dump_ioctl(GPIO_V2_GET_LINEINFO_IOCTL);
    dump_ioctl(GPIO_V2_GET_LINEINFO_WATCH_IOCTL);
    dump_ioctl(GPIO_V2_GET_LINE_IOCTL);
    dump_ioctl(GPIO_GET_LINEINFO_UNWATCH_IOCTL);
    dump_ioctl(GPIO_V2_LINE_SET_CONFIG_IOCTL);
    dump_ioctl(GPIO_V2_LINE_GET_VALUES_IOCTL);
    dump_ioctl(GPIO_V2_LINE_SET_VALUES_IOCTL);

    dump_struct_info(gpiochip_info);
    dump_struct_info(gpio_v2_line_info);
    dump_struct_info(gpio_v2_line_request);
    dump_struct_info(gpio_v2_line_config);
    dump_struct_info(gpio_v2_line_values);
    dump_struct_info(gpio_v2_line_attribute);
    dump_struct_info(gpio_v2_line_config_attribute);
    dump_struct_info(gpio_v2_line_info_changed);
    dump_struct_info(gpio_v2_line_event);

    printf("\"_\":0}\n");

    return EXIT_SUCCESS;
}
