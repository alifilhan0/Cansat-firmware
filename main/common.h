/**********************************************************************************
 * 
 * 
 *  Copyright 2025 Alif Ilhan https://github.com/alifilhan0
 *  Common header file for cansat main firmware. Important functions are delcared here.
 * 
 * 
 **********************************************************************************/
#include <stdio.h>
#include <stdbool.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "driver/i2c_master.h"

/* Definitions */
/* I2C */
#define I2C_MASTER_SCL_IO           CONFIG_I2C_MASTER_SCL
#define I2C_MASTER_SDA_IO           CONFIG_I2C_MASTER_SDA
#define I2C_MASTER_NUM              I2C_NUM_0
#define I2C_MASTER_FREQ_HZ          CONFIG_I2C_MASTER_FREQUENCY
#define I2C_MASTER_TX_BUF_DISABLE   0
#define I2C_MASTER_RX_BUF_DISABLE   0
#define I2C_MASTER_TIMEOUT_MS       1000

/* UART */

#define EX_UART_NUM UART_NUM_0
#define PATTERN_CHR_NUM    (3)         /*!< Set the number of consecutive and identical characters received by receiver which defines a UART pattern*/

#define BUF_SIZE (1024)
#define RD_BUF_SIZE (BUF_SIZE)
static QueueHandle_t uart0_queue;

/* General purpose global variables */

extern float air_temperature;
extern float air_pressure;
extern float altitude;
extern float internal_temperature;
extern float direction;
extern float latitude, longitude;
extern float x, y, z;
extern bool descending;
extern bool landed;
/* Sensor functions */

extern int get_distance(float distance);
extern int get_altitude(float alt);
extern int get_temperature(float temp);
extern int get_gps_cords(float latitude, float longitude, int stats, int hours, int minutes, int seconds);
extern int get_air_pressure(float air_press);
extern int get_10dof(float pitch, float roll, float yaw, float accel_roll, float accel_pitch, float accel_yaw, float mag_roll, float mag_pitch, float mag_yaw);
extern int get_voltage(float voltage);
extern int trigger_buzzer(void);
extern void xBee_command_handler(char* cmd);

struct xBee_data
{
    int id;
    float distance;
    float altitude;
    float gyro_r, gyro_p, gyro_y;
    float latitude, longitude;
    float temperature;
    float pressure;
    float voltage;
    float accel_r, accel_p, accel_y;
    float mag_r, mag_p, mag_y;
    int rotation_rate;
    int gps_stats;
    int hh, mm, ss;
    char state[16];
    char mode[20];
    int pkt_no;
    int gps_hh, gps_mm, gps_ss;
    float gps_altitude;

};
//TODO:- basically all of them for now
/* Mechanism */

extern int check_payload_attached(void);
extern int check_container_attached(void);
extern int check_parafoil(void);
extern int release_parafoil(void);
extern int release_payload(void);
extern int release_container(void);
extern int steer(float degree);
extern int rotate_servo(int number);
/* Radio */
extern int xBee_send(void);
extern int xBee_receive(void);
