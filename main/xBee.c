#include "common.h"

//Populate data to be sent
void send_data(void)
{
    struct xBee_data *data;

    get_altitude(data->altitude);
    get_distance(data->distance);
    get_internal_temperature(data->temperature);
    get_10dof(data->gyro_r, data->gyro_p, data->gyro_y, data->accel_r, data->accel_p, data->accel_y, data->mag_r, data->mag_p, data->mag_y);
    get_air_pressure(data->pressure);
    get_gps_cords(data->latitude, data->longitude, data->gps_stats, data->gps_hh, data->gps_mm, data->gps_ss);

}

void xBee_command_handler(char* cmd)
{

}

void xBee_send(struct xBee_data *data)
{
    char response[200];
    snprintf(response, sizeof(response), "%d, %d:%d:%d, %d, %s, %s, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %d, %d:%d:%d, %f, %f, %f, %d", data->id, data->hh, data->mm, data->ss,data->pkt_no,  data->mode, data->state, data->altitude, data->temperature, data->pressure, data->voltage, data->gyro_r, data->gyro_p, data->gyro_y, data->accel_r, data->accel_p, data->accel_y, data->mag_r, data->mag_p, data->mag_y, data->rotation_rate, data->gps_hh, data->gps_mm, data->gps_ss, data->gps_altitude, data->latitude, data->longitude, data->gps_stats);
    uart_write_bytes(EX_UART_NUM, response, strlen(response));
    data->pkt_no++;
}

void xBee_receive(void)
{
    
}

xBee_init(void)
{

}
