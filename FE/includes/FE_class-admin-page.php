<?php
if (!defined('ABSPATH')) exit;

class MalwareBoardAdminPage {
    public static function add_settings_page() {
        add_options_page(
            'Malware Detection Board API 설정', 
            'MDB API 설정', 
            'manage_options', 
            'mdb-api-settings', 
            [__CLASS__, 'render_settings_page']
        );
    }

    public static function render_settings_page() {
        ?>
        <div class="wrap">
            <h1>Malware Detection Board API 설정</h1>
            <form method="post" action="options.php">
                <?php
                settings_fields('mdb_api_settings_group');
                do_settings_sections('mdb-api-settings');
                submit_button();
                ?>
            </form>
            
            <!-- API 테스트 섹션 추가 -->
            <div class="postbox">
                <div class="hndle"><h2>API 연결 테스트</h2></div>
                <div class="inside">
                    <p>현재 설정된 API 엔드포인트와 API 키의 연결 상태를 확인합니다.</p>
                    <button id="test-api-btn" class="button button-primary">API 연결 테스트</button>
                    <div id="api-test-result" style="margin-top: 15px;"></div>
                </div>
            </div>
        </div>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const testApiBtn = document.getElementById('test-api-btn');
            const apiTestResult = document.getElementById('api-test-result');
            
            if (testApiBtn) {
                testApiBtn.addEventListener('click', function() {
                    testApiBtn.disabled = true;
                    testApiBtn.textContent = '테스트 중...';
                    apiTestResult.innerHTML = '';
                    
                    const nonce = '<?php echo wp_create_nonce('mdb_admin_nonce'); ?>';
                    
                    fetch(ajaxurl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: 'action=mdb_api_test&nonce=' + encodeURIComponent(nonce)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            apiTestResult.innerHTML = '<div class="notice notice-success inline"><p>' + data.message + '</p></div>';
                        } else {
                            apiTestResult.innerHTML = '<div class="notice notice-error inline"><p>' + data.message + '</p></div>';
                        }
                    })
                    .catch(error => {
                        apiTestResult.innerHTML = '<div class="notice notice-error inline"><p>테스트 요청 실패: ' + error.message + '</p></div>';
                    })
                    .finally(() => {
                        testApiBtn.disabled = false;
                        testApiBtn.textContent = 'API 연결 테스트';
                    });
                });
            }
        });
        </script>
        <?php
    }

    public static function register_settings() {
        $settings = [
            'mdb_api_endpoint' => '',
            'mdb_api_key' => '',
            #'mdb_safe_threshold' => 2,
            #'mdb_warning_threshold' => 5,
            #'mdb_danger_threshold' => 7,
            'mdb_auto_send' => 1,
            'mdb_admin_notifications' => 1
        ];

        foreach ($settings as $key => $default) {
            register_setting('mdb_api_settings_group', $key);
        }

        add_settings_section(
            'mdb_api_settings_section', 
            'API 기본 설정', 
            [__CLASS__, 'settings_section_callback'], 
            'mdb-api-settings'
        );

        $fields = [
            ['mdb_api_endpoint', 'API 엔드포인트', 'api_endpoint_callback'],
            ['mdb_api_key', 'API 키', 'api_key_callback'],
            ##['mdb_safe_threshold', '안전 임계값', 'safe_threshold_callback'],
            ##['mdb_warning_threshold', '주의 임계값', 'warning_threshold_callback'],
            ##['mdb_danger_threshold', '위험 임계값', 'danger_threshold_callback'],
            ['mdb_auto_send', '자동 악성코드 검사', 'auto_send_callback'],
            ['mdb_admin_notifications', '관리자 알림', 'admin_notifications_callback']
        ];

        foreach ($fields as $field) {
            add_settings_field(
                $field[0], 
                $field[1], 
                [__CLASS__, $field[2]], 
                'mdb-api-settings', 
                'mdb_api_settings_section'
            );
        }
    }

    public static function settings_section_callback() {
        echo '<p>악성코드 검사 API에 대한 기본 설정을 구성합니다.</p>';
    }

    public static function render_text_input($name, $placeholder, $description) {
        $value = get_option($name, '');
        ?>
        <input 
            type="text" 
            name="<?php echo $name; ?>" 
            value="<?php echo esc_attr($value); ?>" 
            class="regular-text"
            placeholder="<?php echo $placeholder; ?>"
        />
        <p class="description"><?php echo $description; ?></p>
        <?php
    }

    public static function render_number_input($name, $min, $max, $description) {
        $value = get_option($name, 0);
        ?>
        <input 
            type="number" 
            name="<?php echo $name; ?>" 
            value="<?php echo esc_attr($value); ?>" 
            min="<?php echo $min; ?>" 
            max="<?php echo $max; ?>" 
            step="1"
        />
        <p class="description"><?php echo $description; ?></p>
        <?php
    }

    public static function render_checkbox($name, $label, $description) {
        $value = get_option($name, 1);
        ?>
        <label>
            <input 
                type="checkbox" 
                name="<?php echo $name; ?>" 
                value="1" 
                <?php checked(1, $value); ?>
            /> 
            <?php echo $label; ?>
        </label>
        <p class="description"><?php echo $description; ?></p>
        <?php
    }

    public static function api_endpoint_callback() {
        self::render_text_input(
            'mdb_api_endpoint', 
            '예: https://your-malware-api.com/scan', 
            '악성코드 검사를 위한 API 엔드포인트 URL을 입력하세요.'
        );
    }

    public static function api_key_callback() {
        self::render_text_input(
            'mdb_api_key', 
            'API 키를 입력하세요', 
            'API 인증을 위한 키를 입력하세요.'
        );
    }

    #public static function safe_threshold_callback() {
    #    self::render_number_input(
    #        'mdb_safe_threshold', 
    #        0, 
    #        10, 
    #        '0-10 사이의 안전 판정 임계값을 설정하세요.'
    #    );
    #}

    #public static function warning_threshold_callback() {
    #    self::render_number_input(
    #        'mdb_warning_threshold', 
    #        0, 
    #        10, 
    #        '0-10 사이의 주의 판정 임계값을 설정하세요.'
    #    );
    #}

    #public static function danger_threshold_callback() {
    #    self::render_number_input(
    #        'mdb_danger_threshold', 
    #        0, 
    #        10, 
    #        '0-10 사이의 위험 판정 임계값을 설정하세요.'
    #    );
    #}

    public static function auto_send_callback() {
        self::render_checkbox(
            'mdb_auto_send', 
            '게시글 작성 시 자동으로 악성코드 검사 수행', 
            '활성화하면 게시글 작성 즉시 악성코드 검사를 시작합니다.'
        );
    }

    public static function admin_notifications_callback() {
        self::render_checkbox(
            'mdb_admin_notifications', 
            '악성코드 감지 시 관리자에게 이메일 알림', 
            '위험한 게시글 감지 시 관리자에게 이메일로 알림을 보냅니다.'
        );
    }

    public static function ajax_api_test() {
        check_ajax_referer('mdb_admin_nonce', 'nonce');
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => '권한이 없습니다.'));
        }
        $test_result = Malware_API_Handler::test_api_connection();
        if ($test_result['success']) {
            wp_send_json_success(array('message' => $test_result['message'], 'status' => 'success'));
        } else {
            wp_send_json_error(array('message' => $test_result['message'], 'status' => 'error'));
        }
    }

    public static function handle_bulk_action() {
        check_ajax_referer('mdb_bulk_action', 'nonce');
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => '권한이 없습니다.'));
        }
        $action = sanitize_text_field($_POST['action']);
        $post_ids = array_map('intval', $_POST['post_ids']);
        if (empty($post_ids)) {
            wp_send_json_error(array('message' => '선택된 게시글이 없습니다.'));
        }

        global $wpdb;
        $table_name = $wpdb->prefix . 'malware_board';

        switch ($action) {
            case 'rescan':
                $success_count = 0;
                $fail_count = 0;
                foreach ($post_ids as $post_id) {
                    $url = home_url("/?action=view&id={$post_id}");
                    $result = MDBApiHandler::send_to_external_api($post_id, $url);
                    if ($result) {
                        $success_count++;
                        $wpdb->update($table_name, array(
                            'status' => 'pending',
                            'malware_status' => 'pending',
                            'malware_score' => null,
                            'malware_details' => null,
                            'block_reason' => null
                        ), array('id' => $post_id));
                    } else {
                        $fail_count++;
                    }
                }
                wp_send_json_success(array(
                    'message' => "재검사 완료: 성공 {$success_count}개, 실패 {$fail_count}개",
                    'success_count' => $success_count,
                    'fail_count' => $fail_count
                ));
                break;

            case 'force_public':
                $placeholders = implode(',', array_fill(0, count($post_ids), '%d'));
                $sql = "UPDATE {$table_name} 
                        SET status = 'public',
                            malware_status = 'manual',
                            malware_score = 0,
                            block_reason = '관리자에 의해 강제 공개' 
                        WHERE id IN ($placeholders)";
                $wpdb->query($wpdb->prepare($sql, ...$post_ids));
                wp_send_json_success(array(
                    'message' => count($post_ids) . '개의 게시글을 강제 공개했습니다.',
                    'count' => count($post_ids)
                ));
                break;

            case 'force_private':
                $placeholders = implode(',', array_fill(0, count($post_ids), '%d'));
                $sql = "UPDATE {$table_name} 
                        SET status = 'private',
                            malware_status = 'manual',
                            malware_score = 10,
                            block_reason = '관리자에 의해 강제 비공개' 
                        WHERE id IN ($placeholders)";
                $wpdb->query($wpdb->prepare($sql, ...$post_ids));
                wp_send_json_success(array(
                    'message' => count($post_ids) . '개의 게시글을 강제 비공개했습니다.',
                    'count' => count($post_ids)
                ));
                break;

            default:
                wp_send_json_error(array('message' => '알 수 없는 작업입니다.'));
        }
    }

    public static function mdb_diagnostic() {
        check_ajax_referer('mdb_diagnostic_nonce', 'nonce');
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => '권한이 없습니다.'));
        }
        $type = sanitize_text_field($_POST['type']);
        switch ($type) {
            case 'export_debug_info':
                $debug_info = MDBApiHandler::get_debug_info();
                $upload_dir = wp_upload_dir();
                $export_dir = $upload_dir['basedir'] . '/mdb-debug';
                if (!file_exists($export_dir)) {
                    wp_mkdir_p($export_dir);
                }
                $export_file = $export_dir . '/mdb-debug-' . date('Y-m-d-H-i-s') . '.json';
                $full_debug_info = array_merge($debug_info, array(
                    'export_timestamp' => current_time('mysql'),
                    'site_url' => home_url(),
                    'plugin_version' => '1.0.0'
                ));
                $result = file_put_contents($export_file, json_encode($full_debug_info, JSON_PRETTY_PRINT));
                if ($result) {
                    wp_send_json_success(array(
                        'message' => '디버그 정보를 성공적으로 내보냈습니다.',
                        'file_path' => $export_file,
                        'file_url' => str_replace($upload_dir['basedir'], $upload_dir['baseurl'], $export_file)
                    ));
                } else {
                    wp_send_json_error(array('message' => '디버그 정보 내보내기에 실패했습니다.'));
                }
                break;

            default:
                wp_send_json_error(array('message' => '알 수 없는 진단 작업입니다.'));
        }
    }

    public static function init() {
        if (is_admin()) {
            add_action('admin_menu', [__CLASS__, 'add_settings_page']);
            add_action('admin_init', [__CLASS__, 'register_settings']);
            add_action('wp_ajax_mdb_api_test', [__CLASS__, 'ajax_api_test']);
            add_action('wp_ajax_mdb_bulk_action', [__CLASS__, 'handle_bulk_action']);
            add_action('wp_ajax_mdb_diagnostic', [__CLASS__, 'mdb_diagnostic']);
        }
    }
}

add_action('init', [MalwareBoardAdminPage::class, 'init']);
