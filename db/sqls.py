"""
集中存放项目中需要用到的SQL语句
"""


def insert_photo(model, title, description, folder, count, source, date, tags):
    """
    添加写真信息
    """
    sql = "insert into photo (model, title, description, folder, `count`, source, `date`, tags, update_time) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s', now())" \
          % (model, title, description, folder, count, source, date, tags)
    print("@" + sql)
    return sql

def get_photo(folder):
    """
    根据folder查询photo信息
    """
    sql = "select * from photo where `folder` = '" + folder + "'"
    print("@" + sql)
    return sql


def insert_model(name, birthday, figure, job, address, interest, introduction):
    """
    添加模特信息
    """
    sql = "insert into model (`name`,birthday, figure, job, address, interest, introduction) VALUES ('%s','%s','%s','%s','%s','%s','%s')" \
          % (name, birthday, figure, job, address, interest, introduction)
    print("@" + sql)
    return sql


def get_model(name):
    """
    根据名字查询model信息
    """
    sql = "select * from model where `name` = '" + name + "'"
    print("@" + sql)
    return sql


if __name__ == "__main__":
    print(("1,2,3"))
