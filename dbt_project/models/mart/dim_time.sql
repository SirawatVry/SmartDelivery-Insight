with dates as (
    select unnest(
        generate_series(
            date '2016-01-01',
            date '2019-12-31',
            interval '1 day'
        ))::date as date_day
)
select
    date_day as date_id,
    extract('year' from date_day) as year,
    extract('month' from date_day) as month,
    extract('day' from date_day) as day,
    extract(dow from date_day) as day_of_week,
    case 
        when extract('month' from date_day) in (11,12,1) then true
        else false
    end as is_peak_season
from dates

