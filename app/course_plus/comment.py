#coding=utf-8
from flask import Flask, jsonify, abort, g, make_response, request , url_for
from flask.ext.restful import Api, Resource
from flask.ext.httpauth import HTTPBasicAuth
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
from app import app,db,api,auth,getUrlOfKey
import json
import datetime
from simple_result import SimpleResult
from user import User


class Comment(db.Model):
    __tablename__ = 't_comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    topicId = db.Column(db.Integer, ForeignKey('t_topic.id'))
    userId = db.Column(db.Integer, ForeignKey('t_user.id'))
    parentId = db.Column(db.Integer, ForeignKey('t_comment.id'))
    rootId = db.Column(db.Integer, ForeignKey('t_comment.id'))


    def replyCount(self):
        count = Comment.query.filter(Comment.deletedAt == None, Comment.rootId == self.id).count()
        return count

    def author(self):
        author = User.query.get(self.userId)
        return author

    def json(self):
        author = self.author()
        return {
            "id":self.id,
            "content":self.content,
            "replyCount":self.replyCount(),
            "parentId":self.parentId,
            "rootId":self.rootId,
            "replyTime":self.createdAt.strftime('%Y-%m-%d %H:%M:%S'),
            "authorName":author.nickname,
            "authorIcon":getUrlOfKey(author.icon),
            "authorId":self.userId
        }

@app.route('/api/user/comment/postComment', methods=['POST'])
@auth.login_required
def postComment():
    content = request.json.get("content")
    replyId = request.json.get("replyId")
    topicId = request.json.get("topicId")
    user = g.user
    if not topicId or not content:
        abort(400)
    comment = Comment()
    comment.content = content
    comment.parentId = replyId
    comment.topicId = topicId
    comment.createdAt = datetime.datetime.now()
    comment.updatedAt = comment.createdAt
    comment.rootId = findCommentRootId(replyId)    
    comment.userId = user.id
    db.session.add(comment)
    db.session.commit() 
    return (jsonify(comment.json()),200)


@app.route('/api/user/comment/deleteComment', methods=['GET'])
@auth.login_required
def deleteComment():
    commentId = request.args.get("commentId")
    user = g.user
    if not commentId:
        abort(400)
    comment = Comment.query.get(commentId)
    if comment.userId != user.id:
        return (jsonify(SimpleResult(-1,"不能删除其他人的评论").json()),400)
    comment.deletedAt = datetime.datetime.now()
    db.session.add(comment)
    db.session.commit() 
    return (jsonify(SimpleResult(0,"删除成功").json()) ,200)

@app.route('/api/web/comment/getCommentList', methods=['GET'])
def getCommentList():
    page = request.args.get("page")
    limit = request.args.get("limit")
    comment_id = request.args.get("commentId")
    topic_id = request.args.get("topicId")
    if not page or not topic_id or not limit:
        abort(400)
    comments = []
    page = int(page)
    limit = int(limit)
    if comment_id:
        comments = db.session.query(Comment).filter(Comment.deletedAt == None, Comment.rootId == comment_id,Comment.topicId == topic_id).limit(limit).offset(limit * (page-1))
    else:
        comments = db.session.query(Comment).filter(Comment.deletedAt == None, Comment.topicId == topic_id,Comment.rootId == None).limit(limit).offset(limit * (page-1))
    commentsJsonList = []
    for comment in comments:
        commentsJsonList.append(comment.json())
    return (json.dumps(commentsJsonList),200)


def findCommentRootId(replyId):
    if (replyId):
        #寻找该评论
        comment = Comment.query.get(replyId)
        # 如果该评论有父节点，寻找评论父节点
        if comment.parentId:
            return findCommentRootId(comment.parentId)
        else:
            return replyId
    return None


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(SimpleResult(-1,"缺少参数").json()), 400)