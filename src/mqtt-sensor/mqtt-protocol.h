#ifndef __MQTT_PROTOCOL_H__
#define __MQTT_PROTOCOL_H__

#include "net/routing/routing.h"
#include "mqtt.h"
#include "net/ipv6/uip.h"
#include "net/ipv6/uip-icmp6.h"
#include "net/ipv6/sicslowpan.h"
#include <string.h>

static void set_state(enum node_state new_state);
static void mqtt_event(struct mqtt_connection *m, mqtt_event_t event, void *data);

/* -------------------------- */

#define MQTT_CLIENT_BROKER_IP_ADDR  "fd00::1"
#define CONFIG_IP_ADDR_STR_LEN      64
#define DEFAULT_BROKER_PORT         1883

#define STATE_MACHINE_PERIODIC      (10 * CLOCK_SECOND)
#define DEFAULT_PUBLISH_INTERVAL    (30 * CLOCK_SECOND)
#define MAX_TCP_SEGMENT_SIZE        32
#define CLIENT_ID_SIZE              64
#define CONFIGURATION_TOPIC         "configuration"
#define CONFIGURATION_TOPIC_SIZE    14
#define APP_BUFFER_SIZE             512

/* -------------------------- */

static const char *broker_ip = MQTT_CLIENT_BROKER_IP_ADDR;
char broker_address[CONFIG_IP_ADDR_STR_LEN];

enum mqtt_state { 
    MQTT_INIT, MQTT_NET_OK, MQTT_CONNECTING, 
    MQTT_CONNECTED, MQTT_DISCONNECTED = 5
};

static uint8_t mqtt_current_state;
static struct etimer mqtt_periodic_timer;
static struct mqtt_connection conn;
mqtt_status_t status;

static char sensor_type[] = SENSOR_TYPE;
static char client_id[CLIENT_ID_SIZE];
static char configuration_topic[CONFIGURATION_TOPIC_SIZE];
static char data_topic[DATA_TOPIC_SIZE];
static char app_buffer[APP_BUFFER_SIZE];

/* -------------------------- */

static void mqtt_setup() 
{
    // Initialize the ClientID as MAC address of the node and the topic
	snprintf(client_id, CLIENT_ID_SIZE, "%02x%02x%02x%02x%02x%02x", 
        linkaddr_node_addr.u8[0], linkaddr_node_addr.u8[1], linkaddr_node_addr.u8[2], 
        linkaddr_node_addr.u8[5], linkaddr_node_addr.u8[6], linkaddr_node_addr.u8[7]
	);
    sprintf(configuration_topic, "%s", CONFIGURATION_TOPIC);
    sprintf(data_topic, "%s", DATA_TOPIC);

    // Initialize node_id in the sampled data structure using the link-layer address of the node
    node_id_initialization();
}

static void mqtt_initialization() 
{
    // Register the callback to the MQTT events
	mqtt_register(&conn, &mqtt_sensor, client_id, mqtt_event, MAX_TCP_SEGMENT_SIZE);
	
    // Update the state machine
    mqtt_current_state = MQTT_INIT;
    set_state(CONNECTING);

    // Start the MQTT state machine periodic timer
	etimer_set(&mqtt_periodic_timer, STATE_MACHINE_PERIODIC);
}

static void mqtt_event(struct mqtt_connection *m, mqtt_event_t event, void *data)
{
    switch(event) {
        // Node connected successfully to the broker
        case MQTT_EVENT_CONNECTED:
            LOG_INFO("Client connected to the MQTT broker");
            LOG_INFO_("\n");

            mqtt_current_state = MQTT_CONNECTED;
            set_state(CONNECTED);
            process_poll(&mqtt_sensor);     // wake up the node process to schedule the configuration 
            break;

        // Node disconnected from the broker
        case MQTT_EVENT_DISCONNECTED:
            LOG_ERR("Client disconnected from the MQTT broker with exit code %u", *((mqtt_event_t *)data));
            LOG_ERR_("\n");

            mqtt_current_state = MQTT_DISCONNECTED;
            set_state(NOT_CONNECTED);
            process_poll(&mqtt_sensor);     // wake up the node process
            break;

        // Message published successfully
        case MQTT_EVENT_PUBACK:
            LOG_INFO("Message published");
            LOG_INFO_("\n");
            break;

        default:
            LOG_ERR("Client got a unhandled MQTT event: %i", event);
            LOG_ERR_("\n");
            break;
    }
}

static void mqtt_connection_handler() 
{
    // Check the node connectivity
    if (mqtt_current_state == MQTT_INIT) {
        // Reschedule the event timer until connectivity is available
        if (uip_ds6_get_global(ADDR_PREFERRED) == NULL || uip_ds6_defrt_choose() == NULL) {
            LOG_ERR("Client connectivity not available");
            LOG_ERR_("\n");
            etimer_set(&mqtt_periodic_timer, STATE_MACHINE_PERIODIC);
        } else {
            LOG_INFO("Client connectivity available");
            LOG_INFO_("\n");
            mqtt_current_state = MQTT_NET_OK;
        }
    }
    
    // Attempt to connect to the MQTT broker
    if (mqtt_current_state == MQTT_NET_OK) {
        LOG_INFO("Attempt connection to the MQTT broker");
        LOG_INFO_("\n");

        memcpy(broker_address, broker_ip, strlen(broker_ip));
        mqtt_connect(&conn, broker_address, DEFAULT_BROKER_PORT, (DEFAULT_PUBLISH_INTERVAL * 3) / CLOCK_SECOND, MQTT_CLEAN_SESSION_ON);

        mqtt_current_state = MQTT_CONNECTING;
    }
}

/* -------------------------- */

static int mqtt_notify_configuration()
{
    // If the node is connected to the MQTT broker, send the configuration
    if (mqtt_current_state == MQTT_CONNECTED) {
        LOG_INFO("Client is sending its configuration");
        LOG_INFO_("\n");
        
        snprintf(app_buffer, APP_BUFFER_SIZE, "{\"i\":\"%lx\",\"t\":\"%s\",\"s\":%d}", 
            (long unsigned int)sampled_data.node_id, 
            sensor_type,
            sampling_times[current_sampling_time]
        ); 

        mqtt_publish(&conn, NULL, configuration_topic, (uint8_t *)app_buffer, strlen(app_buffer), MQTT_QOS_LEVEL_0, MQTT_RETAIN_OFF);
    } else if (mqtt_current_state == MQTT_DISCONNECTED) {
        LOG_ERR("Client can't send configuration without connection to the MQTT broker");
        LOG_ERR_("\n");	

        return -1;
    }
    
    return 0; 
}

static int mqtt_publish_to_topic() 
{
    // If the node is connected to the MQTT broker, send the message in the global buffer
    if (mqtt_current_state == MQTT_CONNECTED) {
        LOG_INFO("Client is publishing a new message");
        LOG_INFO_("\n");
        
        serialize_sampled_data(app_buffer, APP_BUFFER_SIZE);           
        mqtt_publish(&conn, NULL, data_topic, (uint8_t *)app_buffer, strlen(app_buffer), MQTT_QOS_LEVEL_0, MQTT_RETAIN_OFF);
    } else if (mqtt_current_state == MQTT_DISCONNECTED) {
        LOG_ERR("Client can't send message without connection to the MQTT broker");
        LOG_ERR_("\n");	

        return -1;
    }
    
    return 0;
}

#endif