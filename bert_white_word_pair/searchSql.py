year = 2024
month = 7
date = 24


getAnswerSummary = f'''
SELECT
  b.question_title,
  b.topic_name_set,
  a.summary_content,
  b.first_level_category_name_array,
  b.second_level_category_name_array
from
  (
    SELECT
      content_id,
      summary_content
    FROM
      km_rec.edu_content_summary_pt
    where
      content_type = 'answer'
    limit 10
  ) a
  left join (
    SELECT
      answer_id,
      question_title,
      topic_name_set,
      first_level_category_name_array,
      second_level_category_name_array
    from
      dw_content_answer.dw_answer_pt_info
    where
      p_year = '{year}'
      and p_month = '{month:02}'
      and p_day = '{date:02}'
  ) b on a.content_id = b.answer_id
'''
getArticleSummary = f'''
SELECT
  b.title,
  b.topic_name_set,
  a.summary_content,
  b.first_level_category_name_array,
  b.second_level_category_name_array
from
  (
    SELECT
      content_id,
      summary_content
    FROM
      km_rec.edu_content_summary_pt
    where
      content_type = 'article'
    limit 10
  ) a
  left join (
    SELECT
      article_id,
      title,
      content,
      topic_name_set,
      first_level_category_name_array,
      second_level_category_name_array
    from
      dw_content_article.dw_article_pt_info
    where
      p_year = '{year}'
      and p_month = '{month:02}'
      and p_day = '{date:02}'
  ) b on a.content_id = b.article_id
'''
getAnswerContent = f'''
SELECT
  b.question_title,
  b.topic_name_set,
  regexp_replace(
    regexp_replace(b.content, '<[^>]+>', ''),
    '[\t\n]',
    ''
  ),
  b.first_level_category_name_array,
  b.second_level_category_name_array
from
  (
    SELECT
      cast(content_id as BIGINT) as content_id
    FROM
      dwd_content.dwd_content_label_detail_pt
    WHERE
      p_date = '{year}-{month:02}-{date:02}'
      AND label_code = 'mirror_tag'
      AND content_type = 'answer'
      AND label_value like '%搜索召回%'
      AND is_valid_version = 1
      limit 10
  ) a
  INNER JOIN (
    SELECT
      answer_id,
      content,
      question_title,
      topic_name_set,
      first_level_category_name_array,
      second_level_category_name_array
    from
      dw_content_answer.dw_answer_pt_info
    where
      p_year = '{year}'
      and p_month = '{month:02}'
      and p_day = '{date:02}'
  ) b on a.content_id = b.answer_id
'''
getArticleContent = f'''
SELECT
  b.title,
  b.topic_name_set,
  regexp_replace(
    regexp_replace(b.content, '<[^>]+>', ''),
    '[\t\n]',
    ''
  ),
  b.first_level_category_name_array,
  b.second_level_category_name_array
from
  (
    SELECT
      cast(content_id as BIGINT) as content_id
    FROM
      dwd_content.dwd_content_label_detail_pt
    WHERE
      p_date = '{year}-{month:02}-{date:02}'
      AND label_code = 'mirror_tag'
      AND content_type = 'article'
      AND label_value like '%搜索召回%'
      AND is_valid_version = 1
      limit 10
  ) a
  INNER JOIN (
    SELECT
      article_id,
      title,
      content,
      topic_name_set,
      first_level_category_name_array,
      second_level_category_name_array
    from
      dw_content_article.dw_article_pt_info
    where
      p_year = '{year}'
      and p_month = '{month:02}'
      and p_day = '{date:02}'
  ) b on a.content_id = b.article_id'''
getAnswerQueryContentId = f'''
SELECT
  flow.query as query,
  flow.content_id as content_id
FROM
  (
    SELECT
      *
    FROM
      dwd_flow.dwd_flow_edu_search_detail_pd
    WHERE
      p_date between '{year}-{month-2:02}-{date:02}' and '{year}-{month:02}-{date:02}'
      AND content_type in ('answer', 'PaidAnswer')
      AND queue like '%edu_%'
      AND search_hash_id != ''
      limit 500
  ) as flow
  LEFT JOIN (
    SELECT
      cast(content_id as BIGINT) as content_id,
      content_type,
      p_date
    FROM
      dwd_content.dwd_content_label_detail_pt
    WHERE
      p_date = '{year}-{month:02}-{date:02}'
      AND label_code = 'mirror_tag'
      AND label_value like '%搜索召回%'
      AND is_valid_version = 1
  ) as tag on flow.content_id = tag.content_id
  AND tag.content_type = if (
    flow.content_type = 'PaidAnswer',
    'answer',
    flow.content_type
  )
WHERE
  tag.content_id IS NOT NULL
  and flow.is_click = true
group by
  flow.query,
  flow.content_id
'''
getArticleQueryContentId=f'''
SELECT
  flow.query as query,
  flow.content_id as content_id
FROM
  (
    SELECT
      *
    FROM
      dwd_flow.dwd_flow_edu_search_detail_pd
    WHERE
      p_date between '{year}-{month-2:02}-{date:02}' and '{year}-{month:02}-{date:02}'
      AND content_type in ('article')
      AND queue like '%edu_%'
      AND search_hash_id != ''
      limit 500
  ) as flow
  LEFT JOIN (
    SELECT
      cast(content_id as BIGINT) as content_id,
      content_type,
      p_date
    FROM
      dwd_content.dwd_content_label_detail_pt
    WHERE
      p_date = '{year}-{month:02}-{date:02}'
      AND label_code = 'mirror_tag'
      AND label_value like '%搜索召回%'
      AND is_valid_version = 1
  ) as tag on flow.content_id = tag.content_id
  AND tag.content_type = if (
    flow.content_type = 'PaidAnswer',
    'answer',
    flow.content_type
  )
WHERE
  tag.content_id IS NOT NULL
  and flow.is_click = true
group by
  flow.query,
  flow.content_id
'''
get_all_summary = '''
SELECT
      content_id, summary_content
    FROM
    km_rec.edu_content_summary_pt
'''

if __name__ == '__main__':
    f = f'''p_date between '{year}-{month-2:02}-{date:02}' and '{year}-{month:02}-{date:02}'''
    print(f)