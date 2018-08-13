using ContentCategorisationRepositoryAPI.Models;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SqlClient;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Web.Http;

namespace ContentCategorisationRepositoryAPI.Controllers
{
    [Route("api/[controller]")]
    public class DataStoreController : ApiController
    {
        [HttpGet]
        [Route("getdatafromrepository")]
        public IHttpActionResult GetArticles()
        {
            List<Articles> Articles = new List<Articles>();
            string connectionString = "Data Source=.;initial catalog=ContentCategorizationRepository ; User ID=sa;Password=categorise;Integrated Security=SSPI;";
            using (SqlConnection con = new SqlConnection(connectionString))
            {
                con.Open();
                using (SqlCommand cmd = new SqlCommand("select * from articles", con))
                {
                    using (SqlDataReader reader = cmd.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            Articles.Add(new Models.Articles {
                                   category = reader["category"].ToString(),
                                   article = Encoding.Unicode.GetString((byte[])reader["ArticleContent"])
                            }); //Specify column index 
                        }
                    }
                }
            }
            return Ok(Articles);
        }

        [HttpPost]
        [Route("addtodatarepository")]
        public IHttpActionResult Post(List<Articles> value)
        {
            string query = "INSERT INTO [ContentCategorizationRepository].[dbo].[Articles]([Category],[ArticleContent]) VALUES (@Category,@ArticleContent)";
            string connectionString = "Data Source=.;initial catalog=ContentCategorizationRepository ; User ID=sa;Password=categorise;Integrated Security=SSPI;";
            using (SqlConnection cn = new SqlConnection(connectionString))
            {
                cn.Open();
                foreach (var article in value)
                {
                    using (SqlCommand cmd = new SqlCommand(query, cn))
                    {
                        cmd.Parameters.Add("@Category", SqlDbType.VarChar, 100).Value = article.category;
                        //Bangla contents are stored as byte array in a Image Type column as bangla font doesn't remain the same if we stored in a varchar or nvarchar column
                        cmd.Parameters.Add("@ArticleContent", SqlDbType.Binary).Value = Encoding.Unicode.GetBytes(article.article);
                        cmd.ExecuteNonQuery();
                    }
                }
                cn.Close();
            }
            return Json(new { article = value });
        }


        [HttpGet]
        [Route("getdatafromrepositorybycategory")]
        public IHttpActionResult GetArticlesByCategory(string categories)
        {
            List<Articles> Articles = new List<Articles>();
            string connectionString = "Data Source=.;initial catalog=ContentCategorizationRepository ; User ID=sa;Password=categorise;Integrated Security=SSPI;";
            using (SqlConnection con = new SqlConnection(connectionString))
            {
                con.Open();
                using (SqlCommand cmd = new SqlCommand($"select * from articles where category in ({categories})", con))
                {
                    using (SqlDataReader reader = cmd.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            Articles.Add(new Models.Articles
                            {
                                category = reader["category"].ToString(),
                                article = Encoding.Unicode.GetString((byte[])reader["ArticleContent"])
                            }); //Specify column index 
                        }
                    }
                }
            }
            return Ok(Articles);
        }
    }
}
