import logging

from sqlalchemy.engine import Engine
from sqlalchemy import text

from entity.response import Response


class ResponseRepository:
    __slots__ = ['engine']

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @staticmethod
    def rowmapper(row):
        if row is None:
            return None
        else:
            return Response(row['id'], row['time'], row['name'])

    @staticmethod
    def daomapper(response: Response):
        return {"time": response.time, "name": response.name}

    def save(self, response):
        self.engine.execute(
            text('''
            INSERT INTO public.response(time, name)
            VALUES(:time, :name)
            '''),
            self.daomapper(response)
        )

    def statistics(self):
        stats = self.engine.execute(
            text('''
            SELECT 
            name as name, 
            AVG("time") as "avg_time", 
            stddev_pop("time") "dev_time", 
            COUNT(*) as total,
            ROUND(SUM(CASE WHEN "time" < 1 THEN 1 ELSE 0 END)::decimal/COUNT(*)*100, 2) "0_1",
            ROUND(SUM(CASE WHEN "time" BETWEEN 1 AND 5 THEN 1 ELSE 0 END)::decimal/COUNT(*)*100, 2) "1_5",
            ROUND(SUM(CASE WHEN "time" > 5 THEN 1 ELSE 0 END)::decimal/COUNT(*)*100, 2) "5_"
            FROM public.response
            WHERE date_trunc('day', stamp) = date_trunc('day', now())
            group by name;
            ''')
        ).fetchall()
        return map(
            lambda result: {
                "name": result["name"],
                "average": result["avg_time"],
                "deviation": result["dev_time"],
                "total": result["total"],
                "first_bucket": result["0_1"],
                "second_bucket": result["1_5"],
                "third_bucket": result["5_"],
            },
            stats
        )
