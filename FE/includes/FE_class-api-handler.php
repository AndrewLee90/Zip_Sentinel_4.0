<?php
if (!defined('ABSPATH')) {
    exit;
}

class Malware_API_Handler {
    // 시간 측정 함수 추가
    private static function microtime_float() {
        list($usec, $sec) = explode(" ", microtime());
        return ((float)$usec + (float)$sec);
    }

    public static function send_to_external_api($post_id, $url) {
        // 전체 프로세스 시작 시간 측정
        $start_total_time = self::microtime_float();
        mdb_write_log("🕒 외부 API 전송 프로세스 시작 - 게시글 ID: {$post_id}");

        // API 설정 확인
        $api_endpoint = get_option('mdb_api_endpoint');
        $api_key = get_option('mdb_api_key');
        $timeout = 300; // 5분 타임아웃

        // API 엔드포인트 유효성 검사
        if (empty($api_endpoint)) {
            mdb_write_log("❌ API 엔드포인트가 설정되지 않았습니다.");
            return false;
        }

        // 데이터베이스에서 게시글 정보 조회
        global $wpdb;
        $table = $wpdb->prefix . 'malware_board';
        
        $start_db_fetch_time = self::microtime_float();
        $post = $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$table} WHERE id = %d", $post_id
        ));
        $db_fetch_time = self::microtime_float() - $start_db_fetch_time;
        mdb_write_log("🕒 데이터베이스 조회 소요 시간: {$db_fetch_time}초");

        // 게시글 존재 여부 확인
        if (!$post) {
            mdb_write_log("❌ 게시글 ID {$post_id}를 찾을 수 없음");
            return false;
        }

        // 파일 크기 계산
        $file_size = $post->file_url ? 
            filesize(str_replace(wp_upload_dir()['baseurl'], wp_upload_dir()['basedir'], $post->file_url)) : 
            0;

        mdb_write_log("📊 파일 크기: {$file_size} bytes");
        mdb_write_log("📊 파일 URL: {$post->file_url}");

        // API 요청 헤더 준비
        $start_header_prep_time = self::microtime_float();
        $headers = [
            'Content-Type' => 'application/json'
        ];

        if (!empty($api_key)) {
            $headers['Authorization'] = 'Bearer ' . $api_key;
        }
        $header_prep_time = self::microtime_float() - $start_header_prep_time;
        mdb_write_log("🕒 헤더 준비 소요 시간: {$header_prep_time}초");

        // API 요청 데이터 준비
        $start_data_prep_time = self::microtime_float();
        $post_data = [
            'post_id' => $post_id,
            'post_text' => $post->title . "\n\n" . strip_tags($post->content),
            'download_link' => $post->file_url ?? '',
            'file_size' => $file_size
        ];
        $data_prep_time = self::microtime_float() - $start_data_prep_time;
        mdb_write_log("🕒 데이터 준비 소요 시간: {$data_prep_time}초");

        // API 요청 전송
        $start_api_send_time = self::microtime_float();
        mdb_write_log("📤 API 요청 전송 중 - 게시글 ID: {$post_id}");
        mdb_write_log("🌐 API 엔드포인트: {$api_endpoint}");

        $response = wp_remote_post($api_endpoint, [
            'method' => 'POST',
            'headers' => $headers,
            'body' => json_encode($post_data),
            'timeout' => $timeout,
            'blocking' => true
        ]);
        $api_send_time = self::microtime_float() - $start_api_send_time;
        mdb_write_log("🕒 API 요청 전송 소요 시간: {$api_send_time}초");

        // API 응답 처리
        $start_response_process_time = self::microtime_float();
        
        // 오류 체크
        if (is_wp_error($response)) {
            mdb_write_log("❌ API 요청 실패: " . $response->get_error_message());
            return false;
        }

        $response_code = wp_remote_retrieve_response_code($response);
        $response_body = wp_remote_retrieve_body($response);

        mdb_write_log("📥 API 응답 상세", [
            '상태 코드' => $response_code,
            '응답 본문' => $response_body
        ]);

        // 성공적인 응답 처리
        if ($response_code >= 200 && $response_code < 300) {
            $start_json_parse_time = self::microtime_float();
            $data = json_decode($response_body, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                mdb_write_log("❌ JSON 디코딩 오류 - 게시글 ID: {$post_id}");
                mdb_write_log("❌ 응답 본문: " . $response_body);
                return false;
            }
            $json_parse_time = self::microtime_float() - $start_json_parse_time;
            mdb_write_log("🕒 JSON 파싱 소요 시간: {$json_parse_time}초");

            // 상세 로깅 추가
            mdb_write_log("📊 API 응답 데이터 분석", [
                'malicious_count' => $data['malicious_count'] ?? 'N/A',
                'total_files' => $data['total_files'] ?? 'N/A',
                'risk_level' => $data['risk_level'] ?? 'N/A',
                'risk_level_readable' => $data['risk_level_readable'] ?? 'N/A'
            ]);

            if ($data && isset($data['risk_level'])) {
                $malicious = intval($data['malicious_count'] ?? 0);
                $total = intval($data['total_files'] ?? 0);

                $result_data = [
                    'malicious_count' => $malicious,
                    'total_files' => $total,
                    'risk_level' => $data['risk_level'] ?? '',
                    'risk_level_readable' => $data['risk_level_readable'] ?? '',
                    'vt_report_url' => $data['vt_report_url'] ?? ''
                ];

                // 악성코드 분석 결과 처리
                process_malware_analysis_result(
                    $post_id,
                    $malicious,
                    $data['risk_level_readable'] ?? '',
                    $result_data
                );

                return true;
            }
        }
        // 응답 처리 시간 계산
        $response_process_time = self::microtime_float() - $start_response_process_time;
        mdb_write_log("🕒 응답 처리 소요 시간: {$response_process_time}초");

        // 전체 프로세스 소요 시간 계산
        $total_time = self::microtime_float() - $start_total_time;
        mdb_write_log("🕒 외부 API 전송 프로세스 총 소요 시간: {$total_time}초");

        return false;
    }

    function process_malware_analysis_result($post_id, $malicious_count, $risk_level_readable, $result_data) {
        global $wpdb;

        // 🔄 악성 코드 분석 결과 저장 (메타 및 커스텀 테이블 등)
        update_post_meta($post_id, 'mdb_malicious_count', $malicious_count);
        update_post_meta($post_id, 'mdb_risk_level_readable', $risk_level_readable);
        update_post_meta($post_id, 'mdb_total_files', $result_data['total_files'] ?? 0);
        update_post_meta($post_id, 'mdb_risk_level', $result_data['risk_level'] ?? '');
        update_post_meta($post_id, 'mdb_vt_report_url', $result_data['vt_report_url'] ?? '');

        // 📌 로그 기록
        mdb_write_log("📌 분석 결과 저장 완료 - 게시글 ID: {$post_id}");

        // ✅ 위험도에 따라 게시글 공개 상태(post_status) 자동 조정
        $risk_level = $result_data['risk_level'] ?? '';

        if ($risk_level === '위험') {
            wp_update_post(array(
                'ID' => $post_id,
                'post_status' => 'private'
            ));
            mdb_write_log("🔒 게시글이 위험으로 판단되어 비공개 처리됨 (post_status: private)");
        } elseif ($risk_level === '주의' || $risk_level === '양호') {
            wp_update_post(array(
                'ID' => $post_id,
                'post_status' => 'publish'
            ));
            mdb_write_log("✅ 게시글이 공개 상태로 유지됨 (post_status: publish)");
        } else {
            mdb_write_log("⚠️ 위험도 정보 부족 또는 미분석 상태이므로 post_status 변경 생략");
        }
    }

    // 기존의 다른 메서드들 (ajax_check_post_status 등) 그대로 유지
    public static function ajax_check_post_status() {
        if (!wp_verify_nonce($_POST['nonce'], 'mdb_nonce')) {
            wp_send_json_error(array('message' => '보안 검증 실패'));
            return;
        }
        $post_id = intval($_POST['post_id']);

        global $wpdb;
        $current_status = $wpdb->get_row($wpdb->prepare(
            "SELECT status, malware_status FROM {$wpdb->prefix}malware_board WHERE id = %d",
            $post_id
        ));

        if (!$current_status) {
            wp_send_json_error(array('message' => '게시글을 찾을 수 없습니다.'));
            return;
        }

        // 상태가 변경되었는지 확인
        $status_changed = ($current_status->malware_status !== 'pending');

        wp_send_json_success(array(
            'status_changed' => $status_changed,
            'current_status' => $current_status->status,
            'malware_status' => $current_status->malware_status
        ));
    }
}