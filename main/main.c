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
int cnt = 0;
float max_altitude = 0;
struct xBee_data *data;

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
        .device_address = BMP280_ADDR,
        .scl_speed_hz = I2C_MASTER_FREQ_HZ,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(*bus_handle, &bmp280, dev_handle));

    i2c_device_config_t mpu6050 = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = MPU6050_ADDR,
        .scl_speed_hz = I2C_MASTER_FREQ_HZ,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(*bus_handle, &mpu6050, dev_handle));

    i2c_device_config_t qmc5883 = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = QMC5883_ADDR,
        .scl_speed_hz = I2C_MASTER_FREQ_HZ,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(*bus_handle, &qmc5883, dev_handle));

    i2c_device_config_t dev_config = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = MPU9250_SENSOR_ADDR,
        .scl_speed_hz = I2C_MASTER_FREQ_HZ,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(*bus_handle, &dev_config, dev_handle));
}

void radio_task(void *pvParameters)
{
    while(1)
    {
        if(xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE)
        {
            xSemaphoreTake(xSemaphore);
            xBee_command_handler(cmd);
            xSemaphoreGive(xSemaphore);
        }

    }
}
void ascending_task(void *pvParameters)
{
    struct xBee_data *data;
    while(1)
    {
        if(descending  == false && landed == false) //cansat is not descending
        {
            if(xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE)
            {
                xSemaphoreTake(xSemaphore);
                strcpy(data->state, "ASCEND");
                get_altitude(altitude);
                if(prev_altitude > altitude)
                {
                    cnt++;
                    if(cnt => 10)
                    {
                        descending = true; // since more than 10 counts suggest decreasing altitude, it must be descending
                        max_altitude = altitude;
                    }
                }
                prev_altitude = altitude;
                send_data();
                xSemaphoreGive(xSemaphore);
            }
            else
            {
                /* Wait for the other tasks to finish */
        
            }
        }
    }
}

void descending_task(void *pvParameters)
{
    struct xBee_data *data;
    while(1)
    {
        if(descending == true && landed == false)
        {
            if(xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE)
            {
                xSemaphoreTake(xSemaphore);
                strcpy(data->state, "DESCEND");
                get_altitude(altitude);

                if(altitude =< max_altitude*0.8 && payload_released == false && container_released == false) //release payload at 80% of flight altitude
                {
                    //TODO:- Fix the release algorithms
                    release_payload();
                    printf("Payload release\n");
                    if(check_payload())
                    {
                        payload_released = true;
                        printf("Payload released successfully\n");
                    }
                }

                else if(altitude =< max_altitude*0.8*0.8 && payload_released == true && container_released == false) //release container at 80% of peak altitude
                {
                    release_container();
                    if(check_container())
                    {
                        container_released = true;
                        printf("Container released successfully\n");
                    }
                }

                if(altitude)

                if(altitude == prev_altitude) //Land condition
                {
                    cnt++;
                    if(cnt =>20)
                    {
                        strcpy(data->state, "LANDED");
                        landed = true;
                        trigger_buzzer(); //Audio beacon
                    }
                }
                send_data();
                xSemaphoreGive(xSemaphore);                
                
            }
        }
    }
}

void landed_task(void *pvParameters)
{
    struct xBee_data *data;
    while(1)
    {
        if(landed == true)
        {
            if(xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE)
            {
                xSemaphoreTake(xSemaphore);
                strcpy(data->state, "LANDED");
                send_data();
                xSemaphoreGive(xSemaphore);

            }
        }

    }
}
void app_main(void)
{
    i2c_master_bus_handle_t bus_handle;
    i2c_master_dev_handle_t dev_handle;
    i2c_master_init(&bus_handle, &dev_handle);
    ESP_LOGI(TAG, "I2C initialized successfully");

    uart_config_t uart_config = {
        .baud_rate = 115200,
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
    xTaskCreatePinnedToCore(radio_task, "radio_task", configMINIMAL_STACK_SIZE * 8, NULL, 5, NULL, 1);
    xTaskCreatePinnedToCore(ascending_task, "ascending_task", configMINIMAL_STACK_SIZE * 8, NULL, 5, NULL, 1);
    xTaskCreatePinnedToCore(descending_task, "descending_task", configMINIMAL_STACK_SIZE * 8, NULL, 5, NULL, 1);
    xTaskCreatePinnedToCore(landed_task, "landed_task", configMINIMAL_STACK_SIZE * 8, NULL, 5, NULL, 1);
}
