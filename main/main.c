/**********************************************************************************
 * 
 * 
 *  Copyright 2025 Alif Ilhan https://github.com/alifilhan0
 *  CanSat firmware
 * 
 * 
 *  TODO:- Add mechanism dependent code.
 * 
 * 
 **********************************************************************************/

#include "common.h"

#define RX_BUF_SIZE   100;
static const char *TAG = "CanSat";

SemaphoreHandle_t xSemaphore = NULL;


float air_temperature = 0;
float air_pressure = 0;
float internal_temperature = 0;
float altitude = 0;
float direction = 0;
float x = 0, y = 0, z = 0;
float latitude = 0, longitude = 0;
float prev_altitude = 0;
bool descending = false;
bool landed = false;
bool payload_released = false;
bool container_released = false;
bool parafoil_released = false;
int cnt = 0;
float max_altitude = 0;

static void i2c_master_init(i2c_master_bus_handle_t *bus_handle, i2c_master_dev_handle_t *dev_handle)
{
    i2c_master_bus_config_t bus_config = {
        .i2c_port = I2C_MASTER_NUM,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_config, bus_handle));

    i2c_device_config_t bmp280 = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = 0x58,
        .scl_speed_hz = 400000,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(*bus_handle, &bmp280, dev_handle));

    i2c_device_config_t mpu6050 = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = 0x68,
        .scl_speed_hz = 400000,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(*bus_handle, &mpu6050, dev_handle));

    i2c_device_config_t qmc5883 = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = 0x02,
        .scl_speed_hz = 400000,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(*bus_handle, &qmc5883, dev_handle));
}

void radio_task(void *pvParameters)
{
    char *data = (char *)malloc(RX_BUF_SIZE + 1);
    while(1)
    {

        if(xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE)
        {
            const uint8_t len = uart_read_bytes(1, data, RX_BUF_SIZE, 10 / portTICK_PERIOD_MS);
            if(len > 0)
            {
                data[len] = 0;
                xBee_command_handler(data);
            }
            xSemaphoreGive(xSemaphore);
        }

    }
}
void ascending_task(struct xBee_data *data)
{
    strcpy(data->state, "ASCEND");
    //get_altitude(altitude);
    altitude = data->altitude;
    if(prev_altitude > altitude)
    {
        cnt++;
        if(cnt >= 10)
        {
            descending = true; // since more than 10 counts suggest decreasing altitude, it must be descending
            max_altitude = altitude;
        }
    }
    prev_altitude = altitude;
    xSemaphoreGive(xSemaphore);
}

void descending_task(struct xBee_data *data)
{
    strcpy(data->state, "DESCEND");
    //get_altitude(altitude);

    if(altitude <= max_altitude*0.8 && payload_released == false && container_released == false) //release payload at 80% of flight altitude
    {
        //TODO:- Fix the release algorithms
        release_payload();
        printf("Payload release\n");
        if(check_payload_attached())
        {
            payload_released = true;
            printf("Payload released successfully\n");
        }
        else
        {
            printf("Payload not released!!!\n");
            system_checkup();
        }

        release_parafoil();
        printf("Parafoil release\n");
        if(check_parafoil())
        {
            parafoil_released = true;
            printf("Parafoil released successfully\n");
        }
        else
        {
            printf("Parafoil not released!!!\n");
            system_checkup();
        }
    }

    else if(altitude <= max_altitude*0.8*0.8 && payload_released == true && container_released == false) //release container at 80% of peak altitude
    {
        release_container();
        if(check_container_attached())
        {
            container_released = true;
            printf("Container released successfully\n");
        }
        else
        {
            printf("Container not released!!!\n");
            system_checkup();
        }
    }

    if(altitude == prev_altitude) //Land condition
    {
        cnt++;
        if(cnt >=20)
        {
            strcpy(data->state, "LANDED");
            descending = false;
            landed = true;
            trigger_buzzer(); //Audio beacon
        }
    }
    send_data(data);
    xSemaphoreGive(xSemaphore);

}

void landed_task(struct xBee_data *data)
{
    strcpy(data->state, "LANDED");
    send_data(data);
    xSemaphoreGive(xSemaphore);

}

void cansat_task(void *pvParameters)
{
    struct xBee_data *data;

    while(1)
    {

        if(xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE)
        {

            if(descending == false && landed == false)
            {
                ascending_task(data);
            }

            if(descending == true && landed == false)
            {
                descending_task(data);
            }

            if(descending == false && landed == true)
            {
                landed_task(data);
            }
            xSemaphoreGive(xSemaphore);

        }
    }
}

void app_main(void)
{
    int ret = 0;
    i2c_master_bus_handle_t bus_handle;
    i2c_master_dev_handle_t dev_handle;
    i2c_master_init(&bus_handle, &dev_handle);
    ESP_LOGI(TAG, "I2C initialized successfully");

    uart_config_t uart_config = {
        .baud_rate = 9600,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    
    uart_driver_install(EX_UART_NUM, BUF_SIZE * 2, BUF_SIZE * 2, 20, &uart0_queue, 0);
    uart_param_config(EX_UART_NUM, &uart_config);
    uart_set_pin(EX_UART_NUM, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    ESP_LOGI(TAG, "UART initialized successfully");
    sensor_init();
    xBee_init();
    xSemaphore = xSemaphoreCreateBinary();

    ret = system_checkup();
    if(ret)
    {
        printf("System error detected, abort\n");
        return 0;
    }

    xTaskCreatePinnedToCore(radio_task, "radio_task", configMINIMAL_STACK_SIZE * 8, NULL, 5, NULL, 0);
    xTaskCreatePinnedToCore(cansat_task, "cansat_task", configMINIMAL_STACK_SIZE * 8, NULL, 5, NULL, 1);
}
