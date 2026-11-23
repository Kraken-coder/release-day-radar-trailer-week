SELECT f.title, COUNT(d.india_net_cr) AS days_present,
       CASE WHEN COUNT(d.india_net_cr) = 3 THEN SUM(d.india_net_cr) END AS opening_weekend_cr
FROM films f LEFT JOIN daily_collections d ON f.film_id=d.film_id AND d.day BETWEEN 1 AND 3
GROUP BY f.film_id, f.title;

SELECT f.title, COUNT(c.comment_id) AS trailer_week_comments
FROM films f JOIN trailers t USING (film_id)
LEFT JOIN comments c ON c.film_id=f.film_id
    AND c.published_at >= t.trailer_at AND c.published_at < DATE_ADD(t.trailer_at, INTERVAL 7 DAY)
WHERE t.history_complete AND DATE_ADD(t.trailer_at, INTERVAL 7 DAY) <= f.release_at
GROUP BY f.film_id, f.title
ORDER BY trailer_week_comments DESC;

SELECT f.title, t.trailer_at, f.release_at,
       TIMESTAMPDIFF(HOUR, t.trailer_at, f.release_at) / 24.0 AS lead_days,
       DATE_ADD(t.trailer_at, INTERVAL 7 DAY) > f.release_at AS overlaps_release
FROM films f JOIN trailers t USING (film_id);

SELECT f.language, COUNT(*) AS films
FROM films f
GROUP BY f.language;

SELECT f.title, d.day, d.india_net_cr
FROM films f JOIN daily_collections d USING (film_id)
WHERE d.day BETWEEN 1 AND 3
ORDER BY f.release_at, d.day;

SELECT f.title, t.history_complete,
       SUM(c.in_trailer_week) AS observed_trailer_week_comments,
       COUNT(c.comment_id) AS retrieved_comment_events
FROM films f JOIN trailers t USING (film_id) LEFT JOIN comments c USING (film_id)
GROUP BY f.film_id, f.title, t.history_complete;

SELECT COUNT(*) AS retained_comment_events,
       SUM(in_trailer_week) AS observed_week_events
FROM comments;
