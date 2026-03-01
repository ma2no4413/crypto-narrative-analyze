<?php

// ---------------------------------
// 設定
// ---------------------------------
date_default_timezone_set('Asia/Tokyo');

$apiUrl = 'https://api.coingecko.com/api/v3/coins/markets';
$vsCurrency = 'usd';
$perPage = 250;
$pages = 2; // TOP500

$logFile = __DIR__ . 'logs/market_data.log';

$db = [
    'dsn'  => 'mysql:host=localhost;dbname=market_info;charset=utf8mb4',
    'user' => 'user',
    'pass' => 'pass',
];

// ---------------------------------
// ログ関数
// ---------------------------------
function logMessage($level, $message)
{
    global $logFile;
    $time = date('Y-m-d H:i:s');
    file_put_contents(
        $logFile,
        "[$time][$level] $message\n",
        FILE_APPEND
    );
}

// ---------------------------------
// CoinGecko API 取得
// ---------------------------------
function fetchTokens($page, $maxRetry = 20)
{
    global $apiUrl, $vsCurrency, $perPage;

    $query = http_build_query([
        'vs_currency' => $vsCurrency,
        'order'       => 'market_cap_desc',
        'per_page'    => $perPage,
        'page'        => $page,
        'sparkline'   => 'false',
    ]);

    $url = "$apiUrl?$query";

    $retry = 0;
    $wait  = 2; // 初期待機秒

    while (true) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 30,
            CURLOPT_USERAGENT      => 'market-data-fetcher',
        ]);

        $response = curl_exec($ch);

        if ($response === false) {
            curl_close($ch);
            throw new Exception('cURL error');
        }

        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        // 正常
        if ($status === 200) {
            return json_decode($response, true);
        }

        // Rate Limit
        if ($status === 429 && $retry < $maxRetry) {
            $retry++;
            logMessage(
                'WARN',
                "Rate limit hit (page={$page}). Retry {$retry}/{$maxRetry} after {$wait}s"
            );
            sleep($wait);
            $wait *= 2; // exponential backoff
            continue;
        }

        // その他エラー
        logMessage(
            'ERROR',
            "HTTP {$status} received from CoinGecko (page={$page})"
        );
        throw new Exception("HTTP {$status}");
    }
}


// ---------------------------------
// メイン処理
// ---------------------------------
try {
    logMessage('INFO', 'Start fetching market data');

    $pdo = new PDO(
        $db['dsn'],
        $db['user'],
        $db['pass'],
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]
    );

    // tokens 存在チェック用
    $stmt = $pdo->query("SELECT token_id FROM tokens");
    $existingTokens = array_flip($stmt->fetchAll(PDO::FETCH_COLUMN));

    $snapshotAt = date('Y-m-d H:i:s');

    $insertSql = "
        INSERT INTO market_data (
            token_id,
            snapshot_at,
            market_cap,
            volume_24h
        ) VALUES (
            :token_id,
            :snapshot_at,
            :market_cap,
            :volume_24h
        )
        ON DUPLICATE KEY UPDATE
            market_cap = VALUES(market_cap),
            volume_24h = VALUES(volume_24h)
    ";

    $insertStmt = $pdo->prepare($insertSql);

    $inserted = 0;
    $skipped = 0;
    $rankCount = 1;

    for ($page = 1; $page <= $pages; $page++) {
        $tokens = fetchTokens($page);

        foreach ($tokens as $token) {
            $tokenId = $token['id'];
            // ランキング情報をWARNに出す対応
            // APIから 'market_cap_rank' が取れる場合はそれを使用
            // 取れない場合はループのカウント $rankCount を使用
            $currentRank = $token['market_cap_rank'] ?? $rankCount;

            if (!isset($existingTokens[$tokenId])) {
                logMessage('WARN', "Rank #{$currentRank} | Token not found in tokens table: {$tokenId}");
                $skipped++;
                $rankCount++; // スキップしても順位（カウント）は進める
                continue;
            }

            $insertStmt->execute([
                ':token_id'    => $tokenId,
                ':snapshot_at' => $snapshotAt,
                ':market_cap'  => $token['market_cap'],
                ':volume_24h'  => $token['total_volume'],
            ]);

            $inserted++;
            $rankCount++;
        }

        // rate limit 緩和
        sleep(1);
    }

    logMessage('INFO', "Inserted/Updated: {$inserted}");
    logMessage('INFO', "Skipped (missing tokens): {$skipped}");
    logMessage('INFO', 'Finished successfully');

} catch (Throwable $e) {
    logMessage('ERROR', $e->getMessage());
    exit(1);
}