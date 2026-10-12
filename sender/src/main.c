/*
 * Adapted from Espressif's ESP-CSI csi_send example.
 * SPDX-FileCopyrightText: 2025-2026 Espressif Systems (Shanghai) CO LTD
 * SPDX-License-Identifier: Apache-2.0
 */
#include <stdint.h>
#include <stdbool.h>
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_now.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"

// Both boards must use the same channel and sender address.
static const uint8_t WIFI_CHANNEL = 11;
static const uint8_t SENDER_ADDRESS[6] = {0x1a, 0, 0, 0, 0, 0};
static const uint8_t BROADCAST_ADDRESS[6] = {0xff, 0xff, 0xff, 0xff, 0xff, 0xff};
static const uint32_t PACKET_INTERVAL_MS = 10;

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
    ESP_ERROR_CHECK(esp_wifi_set_mac(WIFI_IF_STA, SENDER_ADDRESS));
    ESP_ERROR_CHECK(esp_wifi_set_bandwidth(WIFI_IF_STA, WIFI_BW_HT20));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    ESP_ERROR_CHECK(esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE));
}

static void configure_packet_broadcast(void)
{
    ESP_ERROR_CHECK(esp_now_init());
    esp_now_peer_info_t broadcast_peer = {
        .peer_addr = {0xff, 0xff, 0xff, 0xff, 0xff, 0xff},
        .channel = WIFI_CHANNEL,
        .ifidx = WIFI_IF_STA,
        .encrypt = false,
    };
    ESP_ERROR_CHECK(esp_now_add_peer(&broadcast_peer));

    // Use an OFDM Wi-Fi rate so the receiver can extract CSI measurements.
    esp_now_rate_config_t transmission_settings = {
        .phymode = WIFI_PHY_MODE_HT20,
        .rate = WIFI_PHY_RATE_MCS0_LGI,
    };
    ESP_ERROR_CHECK(esp_now_set_peer_rate_config(BROADCAST_ADDRESS, &transmission_settings));
}

void app_main(void)
{
    initialize_storage();
    initialize_wifi();
    configure_packet_broadcast();

    uint32_t packet_number = 0;
    while (true) {
        esp_err_t send_result = esp_now_send(BROADCAST_ADDRESS, (const uint8_t *)&packet_number, sizeof(packet_number));
        if (send_result != ESP_OK) {
            ESP_LOGW("sender", "Packet not queued: %s", esp_err_to_name(send_result));
        }
        packet_number++;
        vTaskDelay(pdMS_TO_TICKS(PACKET_INTERVAL_MS));
    }
}
