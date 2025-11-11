/**********************************************************************************
 * 
 * 
 *  Copyright 2025 Alif Ilhan https://github.com/alifilhan0
 *  General mechanism function file
 * 
 * 
 *  TODO:- Add mechanism dependent code
 * 
 * 
 **********************************************************************************/
#include "common.h"

int rotate_servo(int number)
{
    return -1;
}

int steer(float degree)
{
    return -1;
}

int check_container_attached(void)
{
    return -1;
}

int check_payload_attached(void)
{
    return -1;
}

int check_parafoil(void)
{
    return -1;
}

int release_parafoil(void)
{
    return -1;
}

int release_payload(void)
{
    /* Implement Later*/
    return -1;
}

int release_container(void)
{
    /* Implement later */
    return -1;
}

int system_checkup(void)
{

    /* Some checkup will be implemented to help debug and find out system errors */
    /* For now just implementing the print handles as a TODO list */
    printf("sensors online\n");
    printf("steer motors online\n");
    printf("parafoil mechanism online\n");
    printf("payload hook online\n");
    printf("container hook online\n");
    printf("Radio working\n");
    printf("I2C working\n");
    printf("UART working\n");

    printf("sensors offline\n");
    printf("steer motors offline\n");
    printf("parafoil mechanism offline\n");
    printf("payload hook offline\n");
    printf("container hook offline\n");
    printf("Radio not working\n");
    printf("I2C not working\n");
    printf("UART not working\n");
}

int boot_checkup()
{
    /* Initial system checkup every checkup should return 0, else report error and abort*/

    int ret = 0;

    ret = check_container();
    if(ret)
    {
        printf("Container hook not connected. System abort\n");
    }

    ret = check_payload();
    if(ret)
    {
        printf("Payload hook not connected. System abort\n")
    }

    ret = check_parafoil();
    if(ret)
    {
        printf("Parafoil not ready. System abort\n")
    }

    ret = sensor_checkup();
    if(ret)
    {
        printf("steering motors not behaving normally. System abort\n")
    }

    ret = radio_checkup();
    if(ret)
    {
        printf("Radio not working. System abort\n")
    }



}
