#include "contiki.h"
#include "stdio.h"
#include "stdlib.h"

#include "sys/ctimer.h"
#include "os/dev/leds.h"
#include "os/dev/button-hal.h"
#include "sys/log.h"

#ifdef TEMPERATURE_HUMIDITY_CO2
#include "coap-engine.h"
#include "coap-blocking-api.h"
#include "coap-log.h"
extern coap_resource_t res_test;
#endif

#define LOG_MODULE "MQTT Sensor"
#define LOG_LEVEL LOG_LEVEL_INFO

#define BUTTON_PRESS_THRESHOLD	3
#define CONFIGURATION_DELAY		(10 * CLOCK_SECOND)

/* -------------------------- */

static enum node_state { NOT_CONNECTED, CONNECTING, CONNECTED } current_state;
static uint8_t elapsed_seconds_from_press = 0;

static struct etimer configuration_timer;
static struct etimer sampling_timer;
static struct ctimer blinking_timer;
static uint8_t blinking_frequency = 2;

/* -------------------------- */

PROCESS(mqtt_sensor, "MQTT Sensor");
AUTOSTART_PROCESSES(&mqtt_sensor);

#include "mqtt-sensor.h"
#include "mqtt-protocol.h"

static void led_blinking_callback(void *ptr) 
{
	if (current_state == CONNECTING) {
		leds_toggle(LEDS_NUM_TO_MASK(LEDS_RED));
		ctimer_reset(&blinking_timer);
	}
}

static void set_state(enum node_state new_state) 
{
	current_state = new_state;

	switch (new_state) {
		case NOT_CONNECTED: 
			leds_on(LEDS_NUM_TO_MASK(LEDS_RED));
			break;
		case CONNECTING:
			ctimer_set(&blinking_timer, CLOCK_SECOND/blinking_frequency, led_blinking_callback, NULL);
			break;
		case CONNECTED:
			leds_off(LEDS_NUM_TO_MASK(LEDS_RED));
			break;
	}
}

PROCESS_THREAD(mqtt_sensor, ev, data)
{
	PROCESS_BEGIN();

	mqtt_setup();
	mqtt_initialization();

#ifdef TEMPERATURE_HUMIDITY_CO2
	coap_activate_resource(&res_test, "test");
#endif

	while(1) {
		PROCESS_WAIT_EVENT_UNTIL(ev == button_hal_periodic_event || ev == button_hal_release_event || ev == PROCESS_EVENT_POLL || (ev == PROCESS_EVENT_TIMER && (data == &mqtt_periodic_timer || data == &sampling_timer || data == &configuration_timer)));

		// Button release handling
		if (ev == button_hal_release_event) {
			if (elapsed_seconds_from_press < BUTTON_PRESS_THRESHOLD) {
				current_sampling_time = (current_sampling_time + 1) % sampling_times_length; 
				LOG_INFO("Selected sampling time: %d", sampling_times[current_sampling_time]);
				LOG_INFO_("\n");

				// Send the new configuration with a delay if the node is connected to the MQTT broker
				if (current_state == CONNECTED)
					etimer_restart(&configuration_timer);
			}

			elapsed_seconds_from_press = 0;
		} 

		// Button press handling
		else if (ev == button_hal_periodic_event) {
			elapsed_seconds_from_press++;

			if (elapsed_seconds_from_press >= BUTTON_PRESS_THRESHOLD && current_state == NOT_CONNECTED) {
				LOG_INFO("Retrying connection to the MQTT broker");
				LOG_INFO_("\n");
				mqtt_initialization();
			}
		}

		// MQTT events handling
		else if (ev == PROCESS_EVENT_TIMER && data == &mqtt_periodic_timer) {
			mqtt_connection_handler();
    	}

		// MQTT connection and disconnection handling
		else if (ev == PROCESS_EVENT_POLL) {
			if (mqtt_current_state == MQTT_DISCONNECTED) {
				mqtt_connection_handler();
				etimer_stop(&sampling_timer);
			} else if (mqtt_current_state == MQTT_CONNECTED) {
				etimer_set(&configuration_timer, CONFIGURATION_DELAY);
			}
		}

		// Sensing and publishing to the broker
		else if (ev == PROCESS_EVENT_TIMER && data == &sampling_timer) {
			sample_new_data();
			mqtt_publish_to_topic();
			etimer_reset(&sampling_timer);
    	}

		// Notify node configuration and schedule sensor reading
		else if (ev == PROCESS_EVENT_TIMER && data == &configuration_timer) {
			int return_code = mqtt_notify_configuration();

			// Check if the node is connected to the MQTT broker
			if (return_code == 0)
				etimer_set(&sampling_timer, sampling_times[current_sampling_time] * CLOCK_SECOND);
		}
	}

	PROCESS_END();
}
