#include "common.h"

bool simulation_enable = false;
bool simulation_activate = false;

int xBee_command_handler(struct xBee_data *data, char* cmd)
{
    if(simulation_enable == false && simulation_activate == false) {
        if(strstr(cmd, ",SIM,") != NULL)
        {
            if(strstr(cmd, "ENABLE") != NULL) {

                simulation_enable = true;
                strcpy(data->mode, "SIMULATION");
                printf("Simulation mode enabled\n");
                return 0;
            }

        }
    }

    if(simulation_enable == true && simulation_activate == false)
    {
        if(strstr(cmd, ",SIM,") != NULL)
        {
            if(strstr(cmd, "ACTIVATE") !=NULL){

                simulation_activate = true;
                gpio_set_level(10, 1);
                printf("Simulation mode activated\n");
                return 0;
            } else if(strstr(cmd, "DISABLE") != NULL){

                simulation_enable = false;
                strcpy(data->mode, "FLIGHT");
                printf("Simulation mode disabled\n");
                return 0;
            }
        }
    }

    if(simulation_enable == true && simulation_activate == true){
        
        if(strstr(cmd, ",SIMP,") != NULL) {

            int pressure;
            int n = -1;
            n = sscanf(cmd, "CMD,9999,SIMP,%d", &pressure);

            if(n == 1)
            {
                data->pressure = pressure;
                return 0;
            }

        } else if(strstr(cmd, "DEACTIVATE") != NULL){

            simulation_activate = false;
            gpio_set_level(10, 0);
            printf("Simulation mode deactivated\n");
            return 0;
        }
    }

    if(strstr(cmd, ",MEC,") != NULL)
    {
        if(strstr(cmd, ",PAYLOAD,") != NULL)
        {
            if(strstr(cmd, "ON") != NULL) {
                //lock_payload();
            } else if(strstr(cmd, "OFF") != NULL) {
                release_payload();
            }
        }

        else if(strstr(cmd, ",CONTAINER,") != NULL) {

            if(strstr(cmd, "ON") != NULL) {
                //lock_container ();
            } else if(strstr(cmd, "OFF") != NULL) {
                release_container();
            }
        }

        else if(strstr(cmd , ",PARAFOIL,") != NULL) {

            if(strstr(cmd, "ON") != NULL) {
                //lock_parafoil();
            } else if(strstr(cmd, "OFF") != NULL) {
                release_payload();
            }
        }
    }
    return 0;
}

int xBee_send(struct xBee_data *data)
{
    int ret = 0;
    char response[200];
    snprintf(response, sizeof(response), "%d, %d:%d:%d, %d, %s, %s, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %d, %d:%d:%d, %f, %f, %f, %d", data->id, data->hh, data->mm, data->ss,data->pkt_no,  data->mode, data->state, data->altitude, data->temperature, data->pressure, data->voltage, data->gyro_r, data->gyro_p, data->gyro_y, data->accel_r, data->accel_p, data->accel_y, data->mag_r, data->mag_p, data->mag_y, data->rotation_rate, data->gps_hh, data->gps_mm, data->gps_ss, data->gps_altitude, data->latitude, data->longitude, data->gps_stats);
    ret = uart_write_bytes(1, response, strlen(response));

    if(ret)
    {
        printf("failed to send data\n");
        return ret;
    }

    data->pkt_no++;

    return 0;
}

void xBee_init(void)
{

}
