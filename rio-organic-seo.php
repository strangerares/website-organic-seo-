<?php
/**
 * Plugin Name: Rio Organic SEO
 * Description: Create reviewable SEO article and backlink outreach drafts.
 * Version: 0.1.0
 * Requires at least: 6.0
 * Requires PHP: 7.4
 * License: GPL-2.0-or-later
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

final class Rio_Organic_SEO {
	private const OUTREACH_POST_TYPE = 'rio_seo_outreach';

	public function init(): void {
		add_action( 'init', array( $this, 'register_outreach_post_type' ) );
		add_action( 'admin_menu', array( $this, 'register_admin_page' ) );
		add_action( 'add_meta_boxes_post', array( $this, 'add_article_meta_box' ) );
		add_action( 'save_post_post', array( $this, 'save_article_meta' ) );
		add_action( 'admin_post_rio_seo_generate_article', array( $this, 'generate_article' ) );
		add_action( 'admin_post_rio_seo_generate_outreach', array( $this, 'generate_outreach' ) );
	}

	public function register_outreach_post_type(): void {
		register_post_type(
			self::OUTREACH_POST_TYPE,
			array(
				'labels' => array(
					'name'          => 'Outreach drafts',
					'singular_name' => 'Outreach draft',
				),
				'public'       => false,
				'show_ui'      => true,
				'show_in_menu' => 'tools.php',
				'supports'     => array( 'title', 'editor' ),
				'capability_type' => 'post',
				'map_meta_cap' => true,
			)
		);
	}

	public function add_article_meta_box(): void {
		add_meta_box(
			'rio-seo-metadata',
			'Rio Organic SEO',
			array( $this, 'render_article_meta_box' ),
			'post',
			'side'
		);
	}

	public function render_article_meta_box( WP_Post $post ): void {
		wp_nonce_field( 'rio_seo_save_article_meta', 'rio_seo_meta_nonce' );
		?>
		<p>
			<label for="rio-seo-keyword"><strong>Target keyword</strong></label>
			<input id="rio-seo-keyword" name="rio_seo_target_keyword" type="text" class="widefat" value="<?php echo esc_attr( get_post_meta( $post->ID, '_rio_seo_target_keyword', true ) ); ?>">
		</p>
		<p>
			<label for="rio-seo-description"><strong>Suggested meta description</strong></label>
			<textarea id="rio-seo-description" name="rio_seo_meta_description" rows="4" class="widefat"><?php echo esc_textarea( get_post_meta( $post->ID, '_rio_seo_meta_description', true ) ); ?></textarea>
			<span class="description">Copy this into your SEO plugin's description field if needed.</span>
		</p>
		<?php
	}

	public function save_article_meta( int $post_id ): void {
		if (
			! isset( $_POST['rio_seo_meta_nonce'] )
			|| ! is_string( $_POST['rio_seo_meta_nonce'] )
			|| ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['rio_seo_meta_nonce'] ) ), 'rio_seo_save_article_meta' )
			|| ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE )
			|| ! current_user_can( 'edit_post', $post_id )
		) {
			return;
		}

		$keyword     = $this->posted_text( 'rio_seo_target_keyword' );
		$description = $this->posted_text( 'rio_seo_meta_description', true );
		update_post_meta( $post_id, '_rio_seo_target_keyword', sanitize_text_field( $keyword ) );
		update_post_meta( $post_id, '_rio_seo_meta_description', sanitize_textarea_field( $description ) );
	}

	public function register_admin_page(): void {
		add_management_page(
			'Rio Organic SEO',
			'Organic SEO',
			'edit_posts',
			'rio-organic-seo',
			array( $this, 'render_admin_page' )
		);
	}

	public function render_admin_page(): void {
		if ( ! current_user_can( 'edit_posts' ) ) {
			return;
		}

		?>
		<div class="wrap">
			<h1>Rio Organic SEO</h1>
			<p>Create useful, fact-based content as drafts for review. Nothing is published or emailed automatically.</p>
			<?php $this->render_success_notice(); ?>

			<h2>Generate an article draft</h2>
			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
				<input type="hidden" name="action" value="rio_seo_generate_article">
				<?php wp_nonce_field( 'rio_seo_generate_article' ); ?>
				<table class="form-table" role="presentation">
					<tr>
						<th scope="row"><label for="rio-keyword">Primary search topic</label></th>
						<td><input id="rio-keyword" name="keyword" type="text" class="regular-text" required></td>
					</tr>
					<tr>
						<th scope="row"><label for="rio-audience">Intended reader</label></th>
						<td><input id="rio-audience" name="audience" type="text" class="regular-text" required></td>
					</tr>
					<tr>
						<th scope="row"><label for="rio-language">Article language</label></th>
						<td><input id="rio-language" name="language" type="text" class="regular-text" value="English" required></td>
					</tr>
					<tr>
						<th scope="row"><label for="rio-facts">Verified facts and first-hand details</label></th>
						<td>
							<textarea id="rio-facts" name="facts" rows="7" class="large-text" required></textarea>
							<p class="description">Provide accurate details, firsthand expertise, and claims the article may use. The generator is instructed not to invent facts.</p>
						</td>
					</tr>
					<tr>
						<th scope="row"><label for="rio-internal-url">Relevant page on this site</label></th>
						<td><input id="rio-internal-url" name="internal_url" type="url" class="regular-text"></td>
					</tr>
				</table>
				<?php submit_button( 'Generate draft' ); ?>
			</form>

			<hr>
			<h2>Prepare a backlink outreach draft</h2>
			<p>This creates a personalized message for you to review and send yourself. It does not create links, fetch the prospect's site, or send email.</p>
			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
				<input type="hidden" name="action" value="rio_seo_generate_outreach">
				<?php wp_nonce_field( 'rio_seo_generate_outreach' ); ?>
				<table class="form-table" role="presentation">
					<tr>
						<th scope="row"><label for="rio-prospect-url">Prospect website</label></th>
						<td><input id="rio-prospect-url" name="prospect_url" type="url" class="regular-text" required></td>
					</tr>
					<tr>
						<th scope="row"><label for="rio-outreach-url">Page you would like them to consider</label></th>
						<td><input id="rio-outreach-url" name="target_url" type="url" class="regular-text" required></td>
					</tr>
					<tr>
						<th scope="row"><label for="rio-outreach-reason">Why this is relevant to them</label></th>
						<td><textarea id="rio-outreach-reason" name="reason" rows="5" class="large-text" required></textarea></td>
					</tr>
				</table>
				<?php submit_button( 'Create outreach draft' ); ?>
			</form>

			<p>Choose images from your WordPress media library when reviewing an article draft. Use only images you own or have permission to publish.</p>
		</div>
		<?php
	}

	public function generate_article(): void {
		$this->verify_request( 'rio_seo_generate_article' );

		$keyword      = sanitize_text_field( $this->posted_text( 'keyword' ) );
		$audience     = sanitize_text_field( $this->posted_text( 'audience' ) );
		$language     = sanitize_text_field( $this->posted_text( 'language' ) );
		$facts        = sanitize_textarea_field( $this->posted_text( 'facts', true ) );
		$internal_url = $this->validate_site_url( $this->posted_text( 'internal_url' ), false );

		if ( '' === $keyword || '' === $audience || '' === $language || '' === $facts ) {
			wp_die( esc_html__( 'Complete the topic, reader, language, and verified facts fields.', 'rio-organic-seo' ) );
		}
		if ( false === $internal_url ) {
			wp_die( esc_html__( 'The relevant page must be a valid URL on this website.', 'rio-organic-seo' ) );
		}

		$article = $this->request_json(
			'Write a genuinely useful, original SEO article using only the verified facts supplied by the user. Do not invent prices, schedules, credentials, policies, or first-hand experiences. Avoid keyword stuffing, generic filler, and image markup. If an internal page URL is supplied, include one natural link to it. Return JSON with string fields: title, excerpt, body_html, meta_description.',
			wp_json_encode(
				array(
					'website'        => home_url( '/' ),
					'primary_topic'  => $keyword,
					'intended_reader' => $audience,
					'language'       => $language,
					'verified_facts' => $facts,
					'internal_page'  => $internal_url,
					'length'         => 'About 700 words, as appropriate for the topic.',
				)
			)
		);

		foreach ( array( 'title', 'excerpt', 'body_html', 'meta_description' ) as $field ) {
			if ( empty( $article[ $field ] ) || ! is_string( $article[ $field ] ) ) {
				wp_die( esc_html__( 'The AI response did not contain all required article fields. Please try again.', 'rio-organic-seo' ) );
			}
		}

		$post_id = wp_insert_post(
			array(
				'post_type'    => 'post',
				'post_status'  => 'draft',
				'post_title'   => sanitize_text_field( $article['title'] ),
				'post_excerpt' => sanitize_textarea_field( $article['excerpt'] ),
				'post_content' => wp_kses_post( $article['body_html'] ),
			),
			true
		);
		if ( is_wp_error( $post_id ) ) {
			wp_die( esc_html( $post_id->get_error_message() ) );
		}

		update_post_meta( $post_id, '_rio_seo_target_keyword', $keyword );
		update_post_meta( $post_id, '_rio_seo_meta_description', sanitize_text_field( $article['meta_description'] ) );

		wp_safe_redirect( add_query_arg( array( 'page' => 'rio-organic-seo', 'article_id' => $post_id ), admin_url( 'tools.php' ) ) );
		exit;
	}

	public function generate_outreach(): void {
		$this->verify_request( 'rio_seo_generate_outreach' );

		$prospect_url = esc_url_raw( $this->posted_text( 'prospect_url' ) );
		$target_url   = $this->validate_site_url( $this->posted_text( 'target_url' ), true );
		$reason       = sanitize_textarea_field( $this->posted_text( 'reason', true ) );

		if ( ! wp_http_validate_url( $prospect_url ) || false === $target_url || '' === $reason ) {
			wp_die( esc_html__( 'Enter a valid prospect website, a valid page on this site, and a specific reason for reaching out.', 'rio-organic-seo' ) );
		}

		$message = $this->request_json(
			'Write a concise, respectful, personalized collaboration or editorial outreach email. Do not imply an existing relationship, demand a link, offer payment for ranking links, or invent facts about the recipient. Make any link request optional and explain the genuine relevance. Return JSON with string fields: subject and body.',
			wp_json_encode(
				array(
					'prospect_website' => $prospect_url,
					'our_page'         => $target_url,
					'reason_for_contact' => $reason,
				)
			)
		);

		if ( empty( $message['subject'] ) || empty( $message['body'] ) || ! is_string( $message['subject'] ) || ! is_string( $message['body'] ) ) {
			wp_die( esc_html__( 'The AI response did not contain a complete outreach draft. Please try again.', 'rio-organic-seo' ) );
		}

		$post_id = wp_insert_post(
			array(
				'post_type'    => self::OUTREACH_POST_TYPE,
				'post_status'  => 'draft',
				'post_title'   => sanitize_text_field( $message['subject'] ),
				'post_content' => sanitize_textarea_field( $message['body'] ),
			),
			true
		);
		if ( is_wp_error( $post_id ) ) {
			wp_die( esc_html( $post_id->get_error_message() ) );
		}

		update_post_meta( $post_id, '_rio_seo_prospect_url', $prospect_url );
		update_post_meta( $post_id, '_rio_seo_target_url', $target_url );

		wp_safe_redirect( add_query_arg( array( 'page' => 'rio-organic-seo', 'outreach_id' => $post_id ), admin_url( 'tools.php' ) ) );
		exit;
	}

	private function verify_request( string $action ): void {
		if ( ! current_user_can( 'edit_posts' ) ) {
			wp_die( esc_html__( 'You are not allowed to create SEO drafts.', 'rio-organic-seo' ), '', array( 'response' => 403 ) );
		}

		check_admin_referer( $action );
	}

	private function posted_text( string $key, bool $multiline = false ): string {
		if ( ! isset( $_POST[ $key ] ) || ! is_string( $_POST[ $key ] ) ) {
			return '';
		}

		$value = wp_unslash( $_POST[ $key ] );
		return $multiline ? $value : sanitize_text_field( $value );
	}

	private function validate_site_url( string $value, bool $required ) {
		$value = trim( $value );
		if ( '' === $value && ! $required ) {
			return '';
		}
		if ( ! wp_http_validate_url( $value ) ) {
			return false;
		}

		$site_host = wp_parse_url( home_url( '/' ), PHP_URL_HOST );
		$url_host  = wp_parse_url( $value, PHP_URL_HOST );
		if ( ! is_string( $site_host ) || ! is_string( $url_host ) || 0 !== strcasecmp( $site_host, $url_host ) ) {
			return false;
		}

		return esc_url_raw( $value );
	}

	private function request_json( string $system_prompt, string $user_prompt ): array {
		if ( ! defined( 'RIO_SEO_API_KEY' ) || ! is_string( RIO_SEO_API_KEY ) || '' === RIO_SEO_API_KEY ) {
			wp_die( esc_html__( 'AI is not configured. Add RIO_SEO_API_KEY to wp-config.php, then try again.', 'rio-organic-seo' ) );
		}

		$endpoint = defined( 'RIO_SEO_API_URL' ) ? RIO_SEO_API_URL : 'https://api.openai.com/v1/chat/completions';
		$model    = defined( 'RIO_SEO_API_MODEL' ) ? RIO_SEO_API_MODEL : 'gpt-4o-mini';
		if ( ! is_string( $endpoint ) || ! wp_http_validate_url( $endpoint ) || 'https' !== wp_parse_url( $endpoint, PHP_URL_SCHEME ) ) {
			wp_die( esc_html__( 'The AI endpoint must be a valid HTTPS URL.', 'rio-organic-seo' ) );
		}
		if ( ! is_string( $model ) || '' === $model ) {
			wp_die( esc_html__( 'Configure a valid AI model name before generating content.', 'rio-organic-seo' ) );
		}

		$response = wp_remote_post(
			$endpoint,
			array(
				'timeout' => 60,
				'headers' => array(
					'Authorization' => 'Bearer ' . RIO_SEO_API_KEY,
					'Content-Type'  => 'application/json',
				),
				'body' => wp_json_encode(
					array(
						'model'           => $model,
						'response_format' => array( 'type' => 'json_object' ),
						'messages'        => array(
							array( 'role' => 'system', 'content' => $system_prompt ),
							array( 'role' => 'user', 'content' => $user_prompt ),
						),
					)
				),
			)
		);

		if ( is_wp_error( $response ) ) {
			wp_die( esc_html__( 'Could not reach the configured AI service. Check the endpoint and site network settings.', 'rio-organic-seo' ) );
		}

		$status = wp_remote_retrieve_response_code( $response );
		if ( $status < 200 || $status >= 300 ) {
			wp_die( esc_html( sprintf( 'The AI service returned HTTP %d. Check the API key, model, and endpoint configuration.', $status ) ) );
		}

		$decoded = json_decode( wp_remote_retrieve_body( $response ), true );
		$content = $decoded['choices'][0]['message']['content'] ?? null;
		if ( ! is_string( $content ) ) {
			wp_die( esc_html__( 'The AI service returned an unexpected response. Please try again.', 'rio-organic-seo' ) );
		}

		$result = json_decode( $content, true );
		if ( ! is_array( $result ) ) {
			wp_die( esc_html__( 'The AI service did not return valid JSON. Please try again.', 'rio-organic-seo' ) );
		}

		return $result;
	}

	private function render_success_notice(): void {
		$article_id  = absint( $_GET['article_id'] ?? 0 );
		$outreach_id = absint( $_GET['outreach_id'] ?? 0 );

		if ( $article_id ) {
			printf(
				'<div class="notice notice-success"><p>Article draft created. <a href="%s">Review and edit the draft</a>.</p></div>',
				esc_url( get_edit_post_link( $article_id ) )
			);
		} elseif ( $outreach_id ) {
			printf(
				'<div class="notice notice-success"><p>Outreach draft created. <a href="%s">Review the message</a>.</p></div>',
				esc_url( get_edit_post_link( $outreach_id ) )
			);
		}
	}
}

( new Rio_Organic_SEO() )->init();
