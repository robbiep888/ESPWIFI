/*
 * Adapted from Espressif's ESP-CSI csi_recv example.
 * SPDX-FileCopyrightText: 2025-2026 Espressif Systems (Shanghai) CO LTD
 * SPDX-License-Identifier: Apache-2.0
 */
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "nvs_flash.h"
#include "math.h"

// Match the sender's channel and address; the receiver has its own address.
static const uint8_t WIFI_CHANNEL = 11;
static const uint8_t SENDER_ADDRESS[6] = {0x1a, 0, 0, 0, 0, 0};
static const uint8_t RECEIVER_ADDRESS[6] = {0x1a, 0, 0, 0, 0, 1};

static void initialize_storage(void)
{
    esp_err_t storage_result = nvs_flash_init();
    if (storage_result == ESP_ERR_NVS_NO_FREE_PAGES || storage_result == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        storage_result = nvs_flash_init();
    }
    ESP_ERROR_CHECK(storage_result);
}

static void initialize_wifi(void)
{
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    wifi_init_config_t wifi_settings = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_settings));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_mac(WIFI_IF_STA, RECEIVER_ADDRESS));
    ESP_ERROR_CHECK(esp_wifi_set_bandwidth(WIFI_IF_STA, WIFI_BW_HT20));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    ESP_ERROR_CHECK(esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE));
}


static float calculate_amplitude(int8_t imaginary_component, int8_t real_component) {
    float imaginary_value = imaginary_component;
    float real_value = real_component;    
    return sqrtf((float)(imaginary_value * imaginary_value + real_value * real_value));
}


// The Wi-Fi driver calls this function whenever it captures CSI.
static void print_channel_measurements(void *callback_context, wifi_csi_info_t *measurement)
{
    if (measurement == NULL || measurement->buf == NULL || measurement->len == 0) {
        return;
    }
    if (memcmp(measurement->mac, SENDER_ADDRESS, sizeof(SENDER_ADDRESS)) != 0) {
        return;
    }


    if (measurement->len < 6){
    return;
    }

    int8_t imaginary_component = measurement->buf[4];
    int8_t real_component = measurement->buf[5];
    float signal_amplitude = calculate_amplitude(imaginary_component, real_component);

    static uint32_t received_packet_count = 0;

    // Each output row contains: count, signal strength, invalid-data flag, raw CSI.
    /*
    printf("CSI_DATA,%" PRIu32 ",%d,%d,\"[", received_packet_count,
           measurement->rx_ctrl.rssi, measurement->first_word_invalid);
    for (int measurement_index = 0; measurement_index < measurement->len; measurement_index++) {
        if (measurement_index > 0) {
            printf(",");
        }
        printf("%d", measurement->buf[measurement_index]);
    }
    printf("]\"\n");
    */


    printf("Amplitude,%" PRIu32 ",%.2f,%d\n",
       received_packet_count,
       signal_amplitude,
       measurement->rx_ctrl.rssi);
    received_packet_count++;
}

static void start_receiving_measurements(void)
{
    // Listen to packets on this channel without joining a router's network.
    ESP_ERROR_CHECK(esp_wifi_set_promiscuous(true));
    wifi_csi_config_t measurement_settings = {
        .lltf_en = true,
        .htltf_en = true,
        .stbc_htltf2_en = false,
        .ltf_merge_en = true,
        .channel_filter_en = true,
        .manu_scale = false,
        .shift = 0,
    };
    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&measurement_settings));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(print_channel_measurements, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_csi(true));
}



void app_main(void)
{
    initialize_storage();
    initialize_wifi();
    start_receiving_measurements();


    // Start of code

}
