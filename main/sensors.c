/**********************************************************************************
 * 
 * 
 *  Copyright 2025 Alif Ilhan https://github.com/alifilhan0
 *  Sensor interface for CanSat firmware.
 * 
 * 
 **********************************************************************************/

#include "common.h"
#include "bmp280.h"

int get_altitude(float alt)
{
   /* To be implemented after component insertion */
   return alt;
}

int get_temperature(float int_temp)
{
   /* To be implemented after component insertion */
   return int_temp;
}

int get_gps_cords(float latitude, float longitude, int stats, int hours, int minutes, int seconds)
{
   /* To be implemented after component insertion */
   return 0;
}

void populate_data(struct xBee_data *data);
{
   
    int ret = 0;

    ret = get_altitude(data->altitude);
    if(ret)
    {
        printf("failed to get altitude data\n");
        return ret;
    }

    ret = get_distance(data->distance);
    if(ret)
    {
        printf("failed to get distance data\n");
        return ret;
    }

    ret = get_temperature(data->temperature);
    if(ret)
    {
        printf("failed to get temperature data\n");
        return ret;
    }

    ret = get_10dof(data->gyro_r, data->gyro_p, data->gyro_y, data->accel_r, data->accel_p, data->accel_y, data->mag_r, data->mag_p, data->mag_y);
    if(ret)
    {
        printf("failed to get accel, gyro and mag data\n");
        return ret;
    }

    ret = get_air_pressure(data->pressure);
    if(ret)
    {
        printf("failed to get pressure data\n");
        return ret;
    }

    ret = get_gps_cords(data->latitude, data->longitude, data->gps_stats, data->gps_hh, data->gps_mm, data->gps_ss);
    if(ret)
    {
        printf("failed to get gps coordinates\n");
        return ret;
    }
}

void sensor_init(void)
{

}
