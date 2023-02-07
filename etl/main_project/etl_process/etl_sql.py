select_film_works = '''
    SELECT
       fw.id,
       fw.title,
       fw.description,
       fw.rating,
       fw.modified,
       COALESCE (
           json_agg(
               DISTINCT jsonb_build_object(
                   'person_role', pfw.role,
                   'id', p.id,
                   'name', p.full_name
               )
           ) FILTER (WHERE p.id is not null),
           '[]'
       ) as persons,
       array_agg(DISTINCT g.name) as genres
    FROM content.film_work fw
    LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
    LEFT JOIN content.person p ON p.id = pfw.person_id
    LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
    LEFT JOIN content.genre g ON g.id = gfw.genre_id
    WHERE fw.modified >= (%s)
    GROUP BY fw.id
    ORDER BY fw.modified
    LIMIT 50;
'''
select_genres = '''
    SELECT g.id, g.name, g.description
    FROM genre as g
    WHERE id in (SELECT DISTINCT genre_id FROM genre_film_work) 
'''
select_persons = '''
    SELECT p.id, p.full_name, p.modified,
    ARRAY_AGG(DISTINCT person_film_work.role) AS role,
    ARRAY_AGG(DISTINCT person_film_work.film_work_id)::text[] AS film_ids
    FROM content.person as p 
    LEFT OUTER JOIN content.person_film_work 
    ON content.person_film_work.person_id = p.id 
    GROUP BY p.id;
'''
