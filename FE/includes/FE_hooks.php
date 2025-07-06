<?php
if (!defined('ABSPATH')) exit;

class MDBHooks {
    /**
     * 후킹 초기화
     */
    public static function init() {
        // 게시글 작성/수정 후 악성코드 검사 트리거
        add_action('save_post', array(__CLASS__, 'trigger_malware_scan'), 10, 3);
        
        // 주기적 작업 스케줄 등록
        add_action('init', array(__CLASS__, 'register_cron_jobs'));
        
        // 파일 업로드 제한 및 보안 필터
        add_filter('wp_handle_upload_prefilter', array(__CLASS__, 'validate_file_upload'));
        
        // 게시판 페이지 요청 처리
        add_action('init', array(__CLASS__, 'handle_board_page_request'));
        
        // 단축코드 등록 (이미 malware-detection-board.php에서 처리됨)
        
        // 플러그인 로드 시 주기적 작업 확인
        add_action('plugins_loaded', array(__CLASS__, 'check_scheduled_tasks'));
    }
    
    /**
     * 주기적 작업 스케줄 등록
     */
    public static function register_cron_jobs() {
        // 실패한 요청 재시도
        if (!wp_next_scheduled('mdb_retry_analysis')) {
            wp_schedule_event(
                time(), 
                'hourly', 
                'mdb_retry_analysis'
            );
        }
        
        // API 결과 확인
        if (!wp_next_scheduled('mdb_check_api_result')) {
            wp_schedule_event(
                time(), 
                'every_fifteen_minutes', 
                'mdb_check_api_result'
            );
        }
        
        // 오래된 대기 게시글 정리
        if (!wp_next_scheduled('mdb_clear_pending_posts')) {
            wp_schedule_event(
                time(), 
                'daily', 
                'mdb_clear_pending_posts'
            );
        }
    }
    
    /**
     * 주기적 작업 확인 및 실행
     */
    public static function check_scheduled_tasks() {
        // 재시도 로직 실행
        if (get_option('mdb_auto_send', 1)) {
            add_action('mdb_retry_analysis', array('MDBApiHandler', 'retry_failed_requests'));
        }
        
        // API 결과 확인 로직
        add_action('mdb_check_api_result', array(__CLASS__, 'process_pending_posts'));
        
        // 대기 게시글 정리
        add_action('mdb_clear_pending_posts', array(__CLASS__, 'cleanup_old_pending_posts'));
    }
    
    /**
     * 대기 중인 게시글 처리
     */
    public static function process_pending_posts() {
        global $wpdb;
        $table_name = $wpdb->prefix . 'malware_board';
        
        // 30분 이상 대기 중인 게시글 찾기
        $pending_posts = $wpdb->get_results(
            $wpdb->prepare(
                "SELECT id FROM {$table_name} 
                WHERE malware_status = 'pending' 
                AND status = 'pending' 
                AND created_at < %s 
                LIMIT 10",
                date('Y-m-d H:i:s', strtotime('-30 minutes'))
            )
        );
        
        if (empty($pending_posts)) {
            return;
        }
        
        foreach ($pending_posts as $post) {
            // 개별 게시글에 대해 결과 확인 시도
            $result = MDBApiHandler::get_malware_analysis_result($post->id);
            
            if ($result) {
                // 결과가 있으면 처리
                process_malware_analysis_result(
                    $post->id, 
                    intval($result['malware_score']), 
                    isset($result['details']) ? $result['details'] : '',
                    isset($result['items']) ? $result['items'] : array()
                );
            }
        }
    }
    
    /**
     * 오래된 대기 게시글 정리
     */
    public static function cleanup_old_pending_posts() {
        global $wpdb;
        $table_name = $wpdb->prefix . 'malware_board';
        
        // 24시간 이상 대기 중인 게시글 찾기
        $old_pending_posts = $wpdb->get_results(
            $wpdb->prepare(
                "SELECT id FROM {$table_name} 
                WHERE malware_status = 'pending' 
                AND status = 'pending' 
                AND created_at < %s",
                date('Y-m-d H:i:s', strtotime('-24 hours'))
            )
        );
        
        if (empty($old_pending_posts)) {
            return;
        }
        
        foreach ($old_pending_posts as $post) {
            // 해당 게시글을 실패 상태로 업데이트
            $wpdb->update(
                $table_name,
                array(
                    'status' => 'private',
                    'malware_status' => 'failed',
                    'malware_details' => 'API 응답 없음 - 24시간 경과',
                    'block_reason' => '장기 대기로 인한 자동 비공개 처리'
                ),
                array('id' => $post->id)
            );
            
            // 관리자에게 알림
            if (get_option('mdb_admin_notifications', 1)) {
                self::send_long_pending_notification($post->id);
            }
        }
    }
    
    /**
     * 장기 대기 게시글에 대한 알림 이메일
     * @param int $post_id 게시글 ID
     */
    private static function send_long_pending_notification($post_id) {
        global $wpdb;
        $post = $wpdb->get_row(
            $wpdb->prepare(
                "SELECT * FROM {$wpdb->prefix}malware_board WHERE id = %d", 
                $post_id
            )
        );
        
        if (!$post) return;
        
        $admin_email = get_option('admin_email');
        $site_name = get_bloginfo('name');
        $site_url = home_url();
        
        $subject = "[{$site_name}] 장기 대기 게시글 비공개 처리 알림";
        
        $message = "다음 게시글이 24시간 동안 악성코드 검사 대기 상태로 유지되어 자동으로 비공개 처리되었습니다.\n\n";
        $message .= "사이트: {$site_name} ({$site_url})\n";
        $message .= "게시글 ID: {$post_id}\n";
        $message .= "제목: {$post->title}\n";
        $message .= "작성일: {$post->created_at}\n\n";
        $message .= "게시글 확인: " . home_url("/?action=view&id={$post_id}") . "\n";
        $message .= "관리자 페이지: " . admin_url('tools.php?page=mdb-posts') . "\n\n";
        $message .= "이 메일은 자동으로 발송된 메일입니다.";
        
        $headers = array('Content-Type: text/plain; charset=UTF-8');
        wp_mail($admin_email, $subject, $message, $headers);
    }
    
    /**
     * 게시글 작성/수정 시 악성코드 검사 트리거
     * @param int $post_id 게시글 ID
     * @param WP_Post $post 게시글 객체
     * @param bool $update 업데이트 여부
     */
    public static function trigger_malware_scan($post_id, $post, $update) {
        // 자동 검사가 비활성화되었거나 특정 포스트 타입이 아닌 경우 건너뜀
        if (!get_option('mdb_auto_send', 1) || 
            $post->post_type !== 'malware_board' || 
            wp_is_post_revision($post_id)) {
            return;
        }
        
        // 게시글 상태 확인 (자동 저장, 수정 등 제외)
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
        
        // 게시글 내용 확인
        $content = $post->post_content;
        $title = $post->post_title;
        
        // 빈 내용이면 건너뜀
        if (empty(trim($content)) && empty(trim($title))) {
            return;
        }
        
        // 외부 API로 전송
        $url = home_url("/?action=view&id={$post_id}");
        execute_malware_analysis($post_id, $url);
    }
    
    /**
     * 파일 업로드 사전 검증
     * @param array $file 업로드된 파일 정보
     * @return array 수정된 파일 정보
     */
    public static function validate_file_upload($file) {
        // 차단할 확장자 목록 (블랙리스트)
        $blocked_types = array(
            'php', 'php3', 'php4', 'php5', 'phtml', // PHP 실행 파일
            'cgi', 'pl', 'asp', 'aspx', // 서버 스크립트
            'jsp', 'jspx', // Java 서버 페이지
            'htaccess', 'htpasswd', // Apache 설정 파일
            'config', 'conf', 'ini', // 설정 파일
            'dll', 'so', // 시스템 라이브러리
            'exe', 'msi', // 실행 파일
            'bat', 'cmd', // Windows 배치 파일
            'sh', 'bash' // 셸 스크립트
        );
        
        // 현재 파일 확장자 확인
        $file_ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
        
        // 차단된 확장자인지 확인
        if (in_array($file_ext, $blocked_types)) {
            $file['error'] = '보안상의 이유로 해당 파일 형식은 업로드할 수 없습니다.';
            return $file;
        }
        
        // 파일 크기 제한 확인
        $max_upload = min((int)ini_get('upload_max_filesize'), (int)ini_get('post_max_size'));
        $max_size = $max_upload * 1024 * 1024; // 바이트로 변환
        
        if ($file['size'] > $max_size) {
            $file['error'] = sprintf(
                '파일 크기가 너무 큽니다. %dMB 이하의 파일만 업로드 가능합니다.',
                $max_upload
            );
            return $file;
        }
        
        return $file;
    }
    
    /**
     * 게시판 페이지 요청 처리
     */
    public static function handle_board_page_request() {
        // 게시판 페이지 요청 감지
        if (isset($_GET['action']) && in_array($_GET['action'], array('list', 'view', 'write', 'edit'))) {
            // 필요한 경우 사용자 권한 체크
            if ($_GET['action'] === 'write' && !is_user_logged_in()) {
                wp_redirect(wp_login_url());
                exit;
            }
            
            // 사용자 정의 페이지 로드
            add_filter('template_include', array(__CLASS__, 'load_board_template'));
        }
    }
    
    /**
     * 게시판 전용 템플릿 로드
     * @param string $template 현재 템플릿 경로
     * @return string 로드할 템플릿 경로
     */
    public static function load_board_template($template) {
        // 플러그인 디렉토리의 템플릿 파일 경로
        $plugin_template = plugin_dir_path(__FILE__) . 'templates/board-template.php';
        
        // 테마 디렉토리의 커스텀 템플릿 경로
        $theme_template = get_stylesheet_directory() . '/malware-board-template.php';
        
        // 우선순위: 
        // 1. 테마 디렉토리의 커스텀 템플릿
        // 2. 플러그인 디렉토리의 기본 템플릿
        // 3. 현재 템플릿
        if (file_exists($theme_template)) {
            return $theme_template;
        } elseif (file_exists($plugin_template)) {
            return $plugin_template;
        }
        
        return $template;
    }
}
