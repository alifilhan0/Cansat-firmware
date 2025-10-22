#include "common.h"

//Populate data to be sent
void send_data(void)
{
    struct xBee_data *data;

    get_altitude(data->altitude);
    get_distance(data->distance);
    get_internal_temperature(data->temperature);
    get_10dof(data->x, data->y, data->z);
    get_air_pressure(data->pressure);
    compass_get(data->mag_r, data->mag_p, data->mag_y);
    get_gps_cords(data->latitude, data->longitude, data->gpsstats, data->gpstime);

}

void xBee_command_handler(char* cmd)
{

}

void xBee_send(struct xBee_data *data)
{
    
    uart_write_bytes()
}

void xBee_receive(void)
{
    
}

xBee_init(void)
{

}